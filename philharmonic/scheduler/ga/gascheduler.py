import copy
import random

import pandas as pd
import numpy as np

from philharmonic import Schedule, Migration
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

def create_random(environment, cloud):
    unit = ScheduleUnit() # empty schedule unit
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
