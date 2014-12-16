from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler.bcf_scheduler import *
from philharmonic import Schedule, Migration
from philharmonic import conf
import evaluator as ev

class BCFFSScheduler(BCFScheduler):
    """Best Cost Fit Frequency Scaling (BCFFS) scheduling algorithm.
    In the first stage migrates VMs to servers maximising utilisation
    and favouring locations with lower electricity and cooling costs.
    In the second stage, when the maximum allowed rate of migrations is
    reached, scales the frequencies of servers until profit losses exceed
    energy savings.

    """

    def _schedule_frequency_scaling(self):
        # - calculate profit (loss)
        profit = ev.calculate_service_profit(self.cloud, self.environment,
                                             self.schedule, self.t, self.end)
        # - calculate energy cost (saving)
        en_cost = ev.combined_cost(self.cloud, self.environment, self.schedule,
                                   self.el, self.temp, self.t, self.end)
    def reevaluate(self):
        self.schedule = Schedule()
        self._original_vm_hosts = {} # stores original VM allocations
        self.t = self.environment.get_time() # current time
        self.end = self.environment.forecast_end
        self.el, self.temp = self.environment.current_data()
        # get VMs that need to be (re-)allocated
        #  - VMs from boot requests
        requests = self.environment.get_requests()
        VMs = [req.vm for req in requests if req.what == 'boot']
        #  - select VMs on underutilised PMs
        VMs.extend(self._remove_vms_from_underutilised_hosts())
        VMs = sort_vms_big_first(VMs)

        # schedule migrations
        for vm in VMs:
            host = self.find_host(vm)
            if host is None:
                raise Exception("not enough free resources")
            self._place(vm, host, self.t)

        # ...and then frequency scaling
        self._schedule_frequency_scaling()

        return self.schedule
