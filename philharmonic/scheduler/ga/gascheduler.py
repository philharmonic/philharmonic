import copy
import random

import pandas as pd
import numpy as np

from philharmonic import Schedule, Migration
from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler import evaluator
from philharmonic.scheduler import BCFScheduler
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
            try:
                w_util = self.w_util
                w_cost = self.w_cost
                w_sla = self.w_sla
                w_constraint = self.w_constraint
            except AttributeError: # not configured, stick to the defaults
                # fitness function weights - default values
                w_util, w_cost, w_sla, w_constraint = 0.18, 0.17, 0.25, 0.4
            start, end = self.environment.t, self.environment.forecast_end
            # we get new data about the future temp. and el. prices
            el_prices, temperature = self.environment.current_data()
            if self.no_temperature:
                temperature = None # we don't consider the temp. factor
            if self.no_el_price:
                w_util = w_cost + w_util
                w_cost = 0.0 # we don't consider the cost factor
            self.util, self.cost, self.constr, self.sla = evaluator.evaluate(
                self.cloud, self.environment, self, el_prices, temperature,
                start, end
            )
            weighted_sum = (
                w_util * self.util +
                w_cost * self.cost + w_sla * self.sla +
                w_constraint * self.constr
            )
            self.fitness = weighted_sum
            self.rfitness = 1 - self.fitness
            #if len(self.environment.get_requests()) > 0:
            #   import ipdb; ipdb.set_trace()
            if np.isnan(self.fitness):
                #import ipdb; ipdb.set_trace()
                pass
            self.changed = False
        return self.fitness

    def _random_migration(self):
        """Return a migration of a random VM, to a random server at a random
        moment within the forecast horizon."""
        # - pick random moment
        start = self.environment.t
        end = self.environment.forecast_end
        t = random_time(start, end)
        # - pick random VM
        # (among union of all allocs at t and VMRequests)
        vm = random.sample(self.cloud.vms, 1)[0]
        # - pick random server
        server = random.sample(self.cloud.servers, 1)[0]
        new_action = Migration(vm, server)
        return new_action, t

    def mutation(self):
        """Change the unit by changing a random action."""
        self.changed = True
        # copy the ScheduleUnit
        new_unit = copy.copy(self) # maybe just modify this unit?
        # remove one action
        removed_action = None
        removed_t = None
        if len(self.actions) > 0:
            i = random.randint(0, len(self.actions)-1)
            removed_action = self.actions.iloc[i]
            removed_t = self.actions.index[i]
            new_unit.actions = new_unit.actions.drop(removed_t)
        # add new random action
        if len(self.cloud.vms) > 0:
            mutated = False
            tries = 0
            max_tries = 3
            while ((not mutated or
                    (new_action == removed_action and t == removed_t)) and
                   tries < max_tries):
                tries += 1
                new_action, t = self._random_migration()
                mutated = new_unit.add(new_action, t)
        return new_unit

    def crossover(self, other, t=None):
        """Single-point crossover of both parent's actions series."""
        start = self.environment.t
        end = self.environment.forecast_end
        if not t:
            t = random_time(start, end)
        child = copy.copy(self) # TODO: better to create a new unit? state etc.
        child.changed = True
        actions1 = self.actions[:t]
        justabit = pd.offsets.Micro(1)
        actions2 = other.actions[t + justabit:]
        child.actions = pd.concat([actions1, actions2])

        child2 = copy.copy(self) # TODO: better to create a new unit? state etc.
        child2.changed = True
        actions1 = other.actions[:t]
        justabit = pd.offsets.Micro(1)
        actions2 = self.actions[t + justabit:]
        child2.actions = pd.concat([actions1, actions2])
        return child, child2

    def update(self):
        """Update to match the new forecast horizon (current time until the end
        of the forecast). Throw away old actions."""
        if len(self.actions) == 0:
            return
        # throw away old actions
        t = self.environment.t
        end = self.environment.forecast_end
        old_len = len(self.actions)
        self.actions = self.actions[t:end]
        # throy away actions on non-existing vms
        in_vms = self.actions.map(lambda a, vms = self.cloud.vms : a.vm in vms)
        try:
            self.actions = self.actions[in_vms]
        except IndexError:
            pass
        if len(self.actions) != old_len: # the unit has changed
            self.changed = True


    def __repr__(self):
        if self.changed:
            change_mark = '*'
        else:
            change_mark = ''
        try:
            s = ('unit ({fit:.2}: cns={cns:.2}, sla={sla:.2}, ' +
                 'ut={ut:.2}, c={c:.2}){chg}')
            s = s.format(fit=self.fitness, ut=self.util, c=self.cost,
                         cns=self.constr, sla=self.sla, chg=change_mark)
        except:
            s = 'unit (fit: ?){}'.format(change_mark)
            #s += super(ScheduleUnit, self).__repr__()
        return s

def create_random(environment, cloud, no_el_price=False, no_temperature=False):
    """create a random unit"""
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
    # TODO: make sure that this works for other periods (days, minutes etc.)
    max_migrations = plan_duration * len(cloud.vms) // 3
    migration_number = random.randint(min_migrations, max_migrations)
    # generate migration_number of migrations
    times = []
    actions = []
    for i in range(migration_number):
        # - pick random moment
        t = random_time(start, end)
        times.append(t)
        # - pick random VM
        vm = random.sample(cloud.vms, 1)[0]
        # - pick random server
        server = random.sample(cloud.servers, 1)[0]
        action = Migration(vm, server)
        actions.append(action)
    unit.actions = pd.TimeSeries(actions, times, name='actions')
    unit.sort() # TODO: kick out duplicates/overrides like unit.add
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
        self.bcf = BCFScheduler()
        self.bcf.environment = self.environment
        self.bcf.cloud = self.cloud

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
            # randomly create self.num_random_recreate new units
            for i in range(self.num_random_recreate):
                unit = create_random(self.environment, self.cloud,
                    self.no_el_price, self.no_temperature)
                new_random_units.append(unit)
            len_new = len(new_random_units)
            existing_population = existing_population[:-len_new]
            self.population = existing_population + new_random_units
            for unit in existing_population:
                unit.update() # reusing old population, so "move window"

    def _artificially_add_boots(self, num_units):
        """Artificially add Migration actions to satisfy Boot requests to
        random units.

        """
        requests = self.environment.get_requests()
        for request in requests:
            if request.what == 'boot':
                for unit in random.sample(self.population, num_units):
                    server = random.sample(self.cloud.servers, 1)[0]
                    action = Migration(request.vm, server)
                    unit.add(action, self.environment.t)
                    unit.changed = True

    def _termination_condition(self):
        return (self._iteration == self.max_generations)

    def _best_satisfies_constraints(self):
        """Best unit that satisfies hard constraints or None if none do."""
        best = sorted(self.population,
                      key=lambda u : (1 - u.constr, u.rfitness),
                      reverse=True)[0]
        if best.constr == 0:
            return best
        else:
            return None

    def _sweep_reallocate_capacity_constraints(self, schedule):
        self.cloud.reset_to_real()
        for t in schedule.actions.index.unique():
            # TODO: seems that adding to the same schedule affects this loop
            # - maybe add all afterwards
            # TODO: precise indexing, not dict
            # TODO: never directly modify alloc - use place and remove
            if isinstance(schedule.actions[t], pd.Series):
                for action in schedule.actions[t].values:
                    self.cloud.apply(action)
            else:
                action = schedule.actions[t]
                self.cloud.apply(action)
            state = self.cloud.get_current()
            if not state.all_within_capacity():
                for server in self.cloud.servers:
                    while not state.within_capacity(server):
                        # TODO: smarter vm selection - use BFD or sth
                        vm = next(iter(state.alloc[server]))
                        state.remove(vm, server)
                        # place vm elsewhere to fix capacity
                        server = self.bcf.find_host(vm)
                        new_action = Migration(vm, server)
                        # TODO: add only afterwards
                        schedule.add(new_action, t)
                        self.cloud.apply(new_action)
                        schedule.changed = True
        return schedule

    def _add_boot_actions_greedily(self, unit):
        """Take the requests and make sure they are placed on a host
        right away using BCF (if the GA didn't schedule them already)."""
        requests = self.environment.get_requests()
        current_actions = unit.filter_current_actions(
            self.environment.t, self.environment.period
        ).values
        placed_vms = set(act.vm for act in current_actions)
        for request in requests:
            if request.what == 'boot':
                # check if an action with that VM already in the schedule
                if request.vm in placed_vms:
                    continue
                server = self.bcf.find_host(request.vm)
                if server is None:
                    continue # not enough free resources for this VM
                # apply and add action to the schedule
                action = Migration(request.vm, server)
                unit.add(action, self.environment.t)
                self.cloud.apply(action)
                placed_vms.add(request.vm)
                current_actions = np.append(current_actions, action)
                unit.changed = True

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
        #self._artificially_add_boots(num_artificial_boot)

        # TODO: check for deleted VMs and remove these actions

        # main loop TODO: split into smaller functions
        self._iteration = 0
        while True: # get new generation
            # calculate fitness
            for unit in self.population:
                unit.calculate_fitness()

            self._iteration += 1
            debug('- generation {}'.format(self._iteration))

            self.population.sort(key=lambda u : u.fitness, reverse=False)
            debug('  - best fitness: {}'.format(self.population[0].fitness))
            debug('  - wrst {}'.format(repr(self.population[-1])))
            debug('  - best {}'.format(repr(self.population[0])))
            #if self.population[0].fitness == 0.06:
            #    import ipdb; ipdb.set_trace()

            # check termination condition
            if self._termination_condition():
                break

            # recombination
            # TODO: generate two children from one pair
            # choose parents weight. among all
            parents = roulette_selection(self.population, num_children)
            children = []
            for j in range(num_children / 2):
                parent1, parent2 = parents[j], parents[j + 1]
                child, child2 = parent1.crossover(parent2)
                children.append(child)
                children.append(child2)
            # new generation
            self.population = self.population[:-num_children] + children
            # mutation
            for unit in random.sample(self.population, num_mutation):
                unit = unit.mutation()
        if self.greedy_constraint_fix:
            # first try to get best that satisfies hard constraints
            best = self._best_satisfies_constraints()
            if best is None or self.always_greedy_fix:
                # none satisfy hard constraints or we always fix
                debug('- greedy constraint fix')
                best = self.population[0]
                self.cloud.reset_to_real()
                self._add_boot_actions_greedily(best)
                self.cloud.reset_to_real()
                self._sweep_reallocate_capacity_constraints(best)
                best.calculate_fitness()
        else:
            best = self.population[0]
        debug(u' \u2502\n \u2514\u2500\u25BA selected {}'.format(repr(best)))
        # debug unallocated VMs
        if best.constr > 0:
            # something is amiss if the best schedule broke constraints
            #import ipdb; ipdb.set_trace()
            pass
        return best

    def reevaluate(self):
        debug('\nREEVALUATE (t={})\n---------------'.format(self.environment.t))
        return self.genetic_algorithm()

    def debug_population(self):
        self.population.reverse()
        for i, unit in enumerate(self.population):
            fit_descr = ('fit:{:.2} -> util: {:.2}, cost:{:.2},' +
                         'constr:{:.2}, sla: {:.2}').format(
                             unit.fitness, unit.util, unit.cost,
                             unit.constr, unit.sla
                         )
            unit_descr = 'unit {} - {}\n-------\n{}\n\n'.format(
                len(self.population) - i - 1, fit_descr, unit.actions)
            debug(unit_descr)
        self.population.reverse()
        #TODO: print cloud's real state and the requests
