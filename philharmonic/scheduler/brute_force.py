from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration

class BruteForceScheduler(IScheduler):
    """Deterministic brute force scheduler."""

    def _evaluate_schedule(schedule):
        pass

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
