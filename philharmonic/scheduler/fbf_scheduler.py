from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule

class FBFScheduler(IScheduler):
    """First-best-fit scheduler."""

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)

    def reevaluate(self):
        self.schedule = Schedule()
        # get new requests
        # for each request:
        # find the best server
        # add new migration to the schedule
        return self.schedule
