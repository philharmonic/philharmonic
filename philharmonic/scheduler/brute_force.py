from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule

class BruteForceScheduler(IScheduler):
    """Deterministic brute force scheduler."""

    def reevaluate(self):
        """Look at the current state of the Cloud and Environment
        and schedule new/different actions if necessary.

        @returns: a Schedule with a time series of actions

        """
        self.schedule = Schedule()
        return self.schedule
