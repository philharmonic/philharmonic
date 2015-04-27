from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration
from philharmonic.scheduler import evaluator

class BruteForceScheduler(IScheduler):
    """Deterministic brute force scheduler."""

    def _evaluate_schedule(self, schedule):
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
            self.cloud, self.environment, schedule, el_prices, temperature,
            start, end
        )
        weighted_sum = (
            w_util * self.util +
            w_cost * self.cost + w_sla * self.sla +
            w_constraint * self.constr
        )
        return weighted_sum

    
    def reevaluate(self):
        """Look at the current state of the Cloud and Environment
        and schedule new/different actions if necessary.

        @returns: a Schedule with a time series of actions

        """

        # enumerate times
        times = self.environment.forecast_window_index()
        t = times[0]

        actions = []
        # enumerate actions
        # - nothing
        # - migration
        for vm in self.cloud.vms:
            for server in self.cloud.servers:
                # - generate schedule instance
                schedule = Schedule()
                schedule.add(Migration(vm, server), t)
                # - evaluate it
                # - if better than best, keep it
        #  - what
        #  - where

        return schedule
