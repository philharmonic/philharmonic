from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration
from philharmonic import conf

class BCFFSScheduler(IScheduler):
    """Best Cost Fit Frequency Scaling (BCFFS) scheduling algorithm.
    In the first stage migrates VMs to servers maximising utilisation
    and favouring locations with lower electricity and cooling costs.
    In the second stage, when the maximum allowed rate of migrations is
    reached, scales the frequencies of servers until profit losses exceed
    energy savings.

    """
    def reevaluate(self):
        self.schedule = Schedule()
        return self.schedule
