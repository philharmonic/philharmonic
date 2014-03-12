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
        super(ScheduleUnit, self).__init__()

    def calculate_fitness(self):
        if self.changed:
            #TODO: maybe move this method to the Scheduler
            #TODO: set start, end
            w_cost, w_sla, w_constraint = 0.3, 0.3, 0.4
            start, end = self.environment.t, self.environment.forecast_end
            el_prices, temperature = self.environment.current_data()
            cost = evaluator.normalised_combined_cost(
                self.cloud, self.environment, self, el_prices, temperature,
                start, end
            )
            sla_penalty = evaluator.calculate_sla_penalties(
                self.cloud, self.environment, self
            )
            constraint_penalty = evaluator.calculate_constraint_penalties(
                self.cloud, self.environment, self
            )
            weighted_sum = (
                w_cost * cost + w_sla * sla_penalty
                + w_constraint * constraint_penalty
            )
            self.fitness = weighted_sum
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

def create_random(environment, cloud):
    # TODO: maybe kick out migrations that make no sense
    unit = ScheduleUnit() # empty schedule unit
    unit.environment = environment
    unit.cloud = cloud
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


class GAScheduler(IScheduler):
    """Genetic algorithm scheduler."""

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)
        self.population_size = 20
        self.recombination_rate = 0.15
        self.mutation_rate = 0.05
        self.generation_num = 3

    def initialize(self):
        evaluator.precreate_synth_power( # need this for efficient schedule eval
            self.environment.start, self.environment.end, self.cloud.servers
        )

    def genetic_algorithm(self):
        # TODO: parameters in conf


        num_children = int(round(self.population_size * self.recombination_rate))
        num_mutation = int(round(self.population_size *self.mutation_rate))

        start = self.environment.t
        end = self.environment.forecast_end

        try: # prepare old population for the new environment
            existing_population = self.population
            # TODO: if reusing old population, move window
        except AttributeError: # initial population generation
            self.population = []
            for i in range(self.population_size):
                unit = create_random(self.environment, self.cloud)
                self.population.append(unit)
        else:
            for unit in existing_population:
                unit.update()

        # TODO: check for deleted VMs and remove these actions

        # main loop TODO: split into smaller functions
        i = 0
        while True: # get new generation
            debug('- generation {}'.format(i))
            # calculate fitness
            for unit in self.population:
                unit.calculate_fitness()

            self.population.sort(key=lambda u : u.fitness, reverse=False)
            debug('  - best fitness: {}'.format(self.population[0].fitness))

            # check termination condition
            if i == self.generation_num:
                break
            i += 1

            # recombination
            parents = self.population[:num_children]
            children = []
            for j in range(num_children):#TODO: choose parents weight. among all
                parent1, parent2 = random.sample(parents, 2)
                child = parent1.crossover(parent2)
                children.append(child)
            # new generation
            self.population = self.population[:-num_children] + children
            # mutation
            for unit in random.sample(self.population, num_mutation):
                unit = unit.mutation()

        # TODO: return best that satisfies hard constraints
        return self.population[0]

    def reevaluate(self):
        debug('\nREEVALUATE (t={})\n---------------'.format(self.environment.t))
        return self.genetic_algorithm()
