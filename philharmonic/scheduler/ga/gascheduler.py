import copy
import random

import pandas as pd
import numpy as np

from philharmonic import Schedule, Migration
from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler.evaluator import normalised_combined_cost
from philharmonic import random_time

class ScheduleUnit(Schedule):
    def calculate_fitness(self):
        now = self.environment.t
        #TODO: maybe move this method to the Scheduler
        el_prices = self.environment.current_data()
        normalised_cost = normalised_combined_cost(self.cloud, self.environment,
                                                   self, el_prices)
        # TODO: add constraint and SLA penalties
        return normalised_cost

    def mutation(self):
        # copy the ScheduleUnit
        new_unit = copy.copy(self)
        # remove one action
        i = random.randint(0, len(self.actions)-1)
        new_unit.actions = new_unit.actions.drop(self.actions.index[i])
        # add new random action
        # - pick random moment
        start = self.environment.t
        end = self.environment.forecast_end
        t = random_time(start, end)
        # - pick random VM (among union of all allocs at t and VMRequests)
        vm = random.sample(self.environment.VMs, 1)[0]
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
        actions1 = self.actions[:t]
        justabit = pd.offsets.Micro(1)
        actions2 = other.actions[t + justabit:]
        child.actions = pd.concat([actions1, actions2])
        return child

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
    max_migrations = plan_duration * len(environment.VMs)
    migration_number = random.randint(min_migrations, max_migrations)
    # generate migration_number of migrations
    for i in range(migration_number):
        # - pick random moment
        t = random_time(start, end)
        # - pick random VM
        vm = random.sample(environment.VMs, 1)[0]
        # - pick random server
        server = random.sample(cloud.servers, 1)[0]
        action = Migration(vm, server)
        unit.add(action, t)
    return unit


class GAScheduler(IScheduler):
    """Genetic algorithm scheduler."""

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)

    def genetic_algorithm(self):
        # TODO: parameters in conf
        population_size = 20
        recombination_rate = 0.15
        mutation_rate = 0.05
        generation_num = 3

        num_children = int(round(population_size * recombination_rate))
        num_mutation = int(round(population_size *mutation_rate))

        # initial population generation - TODO: take existing pop.
        population = []
        for i in range(population_size):
            unit = create_random(self.environment, self.cloud)
            population.append(unit)

        # main loop TODO: split into smaller functions
        termination = False
        i = 0
        while not termination: # get new generation
            # calculate fitness
            for unit in population:
                unit.fitness = unit.calculate_fitness()
            # recombination
            population.sort(key=lambda u : u.fitness, reverse=True)
            parents = population[:num_children]
            children = []
            for j in range(num_children): # TODO: choose parents weighted among all
                parent1, parent2 = random.sample(parents, 2)
                child = parent1.crossover(parent2)
                children.append(child)
            # new generation
            population = population[:-num_children] + children
            # mutation
            for unit in random.sample(population, num_mutation):
                unit = unit.mutation()

            i += 1
            if i == generation_num:
                termination = True

    def reevaluate(self):
        self.genetic_algorithm()
        pass # return schedule
