import copy
import random

import pandas as pd
import numpy as np

from philharmonic import Schedule, Migration
from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler import evaluator
from philharmonic import random_time
from philharmonic.logger import *

class ScheduleUnit(Schedule):

    def __init__(self):
        self.changed = True
        self.no_temperature = False
        self.no_el_price = False
        super(ScheduleUnit, self).__init__()

    #TODO: make operators functions, not methods
    # - they should not have no_temperature and no_el_price references
    def calculate_fitness(self):
        """0.0 is best, 1.0 is worst."""
        if self.changed:
            #TODO: maybe move this method to the Scheduler
            #TODO: set start, end for sla, constraint
            w_util, w_cost, w_sla, w_constraint = 0.18, 0.17, 0.25, 0.4
            start, end = self.environment.t, self.environment.forecast_end
            el_prices, temperature = self.environment.current_data()
            #if len(self.environment.get_requests()) > 0:
            #    import ipdb; ipdb.set_trace()
            if self.no_temperature:
                temperature = None # we don't consider the temp. factor
            if self.no_el_price:
                w_util = w_cost + w_util
                w_cost = 0.0 # we don't consider the cost factor
            self.util, self.cost, self.constraint, self.sla = evaluator.evaluate(
                self.cloud, self.environment, self, el_prices, temperature,
                start, end
            )
            weighted_sum = (
                w_util * self.util +
                w_cost * self.cost + w_sla * self.sla
                + w_constraint * self.constraint
            )
            self.fitness = weighted_sum
            self.rfitness = 1 - self.fitness
            if np.isnan(self.fitness):
                #import ipdb; ipdb.set_trace()
                pass
            self.changed = False
        return self.fitness

    def mutation(self):
        self.changed = True
        # copy the ScheduleUnit
        new_unit = copy.copy(self)
        # remove one action
        if len(self.actions) > 0:
            i = random.randint(0, len(self.actions)-1)
            new_unit.actions = new_unit.actions.drop(self.actions.index[i])
        # add new random action
        if len(self.cloud.vms) > 0:
            # - pick random moment
            start = self.environment.t
            end = self.environment.forecast_end
            t = random_time(start, end)
            # - pick random VM (among union of all allocs at t and VMRequests)
            vm = random.sample(self.cloud.vms, 1)[0]
            # - pick random server
            server = random.sample(self.cloud.servers, 1)[0]
            new_action = Migration(vm, server)
            new_unit.add(new_action, t)
        return new_unit

    def crossover(self, other, t=None):
        """single-point crossover of both parent's actions series"""
        start = self.environment.t
        end = self.environment.forecast_end
        if not t:
            t = random_time(start, end)
        child = copy.copy(self)
        child.changed = True
        actions1 = self.actions[:t]
        justabit = pd.offsets.Micro(1)
        actions2 = other.actions[t + justabit:]
        child.actions = pd.concat([actions1, actions2])
        return child

    def update(self):
        self.changed = True
        if len(self.actions) == 0:
            return
        # throw away old actions
        t = self.environment.t
        end = self.environment.forecast_end
        self.actions = self.actions[t:end]
        # throy away actions on non-existing vms
        in_vms = self.actions.map(lambda a, vms=self.cloud.vms: a.vm in vms)
        try:
            self.actions = self.actions[in_vms]
        except IndexError:
            pass


    def __repr__(self):
        try:
            s = 'unit ({:.2})'.format(self.fitness)
        except:
            s = 'unit (fit: ?)'
            #s += super(ScheduleUnit, self).__repr__()
        return s

def create_random(environment, cloud, no_el_price=False, no_temperature=False):
    # TODO: maybe kick out migrations that make no sense
    unit = ScheduleUnit() # empty schedule unit
    unit.environment = environment
    unit.cloud = cloud
    unit.no_el_price = no_el_price
    unit.no_temperature = no_temperature
    start = environment.t
    end = environment.forecast_end
    min_migrations = 0
    plan_duration = (end - start).total_seconds()
    plan_duration = int(plan_duration / 3600) # in hours
    max_migrations = plan_duration * len(cloud.vms) // 3
    migration_number = random.randint(min_migrations, max_migrations)
    # generate migration_number of migrations
    for i in range(migration_number):
        # - pick random moment
        t = random_time(start, end)
        # - pick random VM
        vm = random.sample(cloud.vms, 1)[0]
        # - pick random server
        server = random.sample(cloud.servers, 1)[0]
        action = Migration(vm, server)
        unit.add(action, t)
    return unit

def roulette_selection(individuals, k):
    """Select *k* individuals from the input *individuals* using *k*
    spins of a roulette. The selection is made by at the rfitness attributes,
    assuming that rfitness approaches 1.0 for the best units
    and 0.0 for the worst. Modified from the DEAP source code.

    @param individuals: A list of individuals to select from by rfitness.
    @param k: The number of individuals to select.
    @returns: A list of selected individuals.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.

    .. warning::
       The roulette selection by definition cannot be used for minimization 
       or when the fitness can be smaller or equal to 0.
    """
    s_inds = sorted(individuals, key=lambda u : u.rfitness, reverse=True)
    sum_fits = sum(ind.rfitness for ind in individuals)

    chosen = []
    for i in range(k):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += ind.rfitness
            if sum_ > u:
                chosen.append(ind)
                break

    return chosen


class GAScheduler(IScheduler):
    """Genetic algorithm scheduler."""

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)
        self.population_size = 20
        self.recombination_rate = 0.15
        self.mutation_rate = 0.05
        self.max_generations = 3
        self.random_recreate_ratio = 0.3
        self.artificial_boot_ratio = 0.15
        self.no_temperature = False
        self.no_el_price = False

    def initialize(self):
        evaluator.precreate_synth_power( # need this for efficient schedule eval
            self.environment.start, self.environment.end, self.cloud.servers
        )

    def _create_or_update_population(self):
        """Initialise population or bring the old one to the new generation
        by updating old units and switching the worst units with randomly
        generated ones.

        """
        try: # prepare old population for the new environment if it exists
            existing_population = self.population
        except AttributeError: # doesn't exist -> initial population generation
            self.population = []
            for i in range(self.population_size):
                unit = create_random(self.environment, self.cloud,
                                     self.no_el_price, self.no_temperature)
                self.population.append(unit)
        else:
            new_random_units = []
            for i in range(self.num_random_recreate):
                unit = create_random(self.environment, self.cloud,
                    self.no_el_price, self.no_temperature)
                new_random_units.append(unit)
            len_new = len(new_random_units)
            existing_population = existing_population[:-len_new]
            self.population = existing_population + new_random_units
            for unit in existing_population:
                unit.update() # reusing old population, so "move window"
            #TODO: randomly create self.num_random_recreate new units

    def _artificially_add_boots(self, num_units):
        """Artificially add Migration actions to satisfy Boot requests to
        random units.

        """
        requests = self.environment.get_requests()
        for request in requests:
            if request.what == 'boot':
                for unit in random.sample(self.population, num_units):
                    # TODO: maybe smarter server selection
                    server = random.sample(self.cloud.servers, 1)[0]
                    action = Migration(request.vm, server)
                    unit.add(action, self.environment.t)

    def genetic_algorithm(self):
        """Propagate through generations, evolve ScheduleUnits and find
        the fittest one.

        """
        num_children = int(round(self.population_size *
                                 self.recombination_rate))
        num_mutation = int(round(self.population_size *self.mutation_rate))
        self.num_random_recreate = int(round(self.population_size *
                                             self.random_recreate_ratio))
        num_artificial_boot = int(round(self.population_size *
                                        self.artificial_boot_ratio))

        start = self.environment.t
        end = self.environment.forecast_end

        self._create_or_update_population()

        # if there are any new boot requests, artificially add them
        self._artificially_add_boots(num_artificial_boot)

        # TODO: check for deleted VMs and remove these actions

        # main loop TODO: split into smaller functions
        i = 0
        while True: # get new generation
            # calculate fitness
            for unit in self.population:
                unit.calculate_fitness()

            self.population.sort(key=lambda u : u.fitness, reverse=False)
            debug('  - best fitness: {}'.format(self.population[0].fitness))
            #if self.population[0].fitness == 0.06:
            #    import ipdb; ipdb.set_trace()

            i += 1
            debug('- generation {}'.format(i))
            # check termination condition
            if i == self.max_generations:
                break

            #import ipdb; ipdb.set_trace()

            # recombination
            # TODO: generate two children from one pair
            # choose parents weight. among all
            parents = roulette_selection(self.population, num_children*2)
            children = []
            for j in range(num_children):
                parent1, parent2 = parents[j], parents[j + 1]
                child = parent1.crossover(parent2)
                children.append(child)
            # new generation
            self.population = self.population[:-num_children] + children
            # mutation
            for unit in random.sample(self.population, num_mutation):
                unit = unit.mutation()

        # TODO: return best that satisfies hard constraints
        #import ipdb; ipdb.set_trace()
        return self.population[0]

    def reevaluate(self):
        debug('\nREEVALUATE (t={})\n---------------'.format(self.environment.t))
        return self.genetic_algorithm()

    def debug_population(self):
        self.population.reverse()
        for unit in self.population:
            fitness_descr = 'fit:{:.2}, util: {}, cost:{}, constr:{}, sla:{}'.format(
                unit.fitness, unit.util, unit.cost, unit.constraint, unit.sla)
            unit_descr = 'unit - {}\n-----\n{}\n\n'.format(
                fitness_descr, unit.actions)
            debug(unit_descr)
        self.population.reverse()
        #TODO: print cloud's real state and the requests
