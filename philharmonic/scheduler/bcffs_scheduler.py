from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler.bcf_scheduler import *
from philharmonic import Schedule, Migration
from philharmonic import conf

class BCFFSScheduler(BCFScheduler):
    """Best Cost Fit Frequency Scaling (BCFFS) scheduling algorithm.
    In the first stage migrates VMs to servers maximising utilisation
    and favouring locations with lower electricity and cooling costs.
    In the second stage, when the maximum allowed rate of migrations is
    reached, scales the frequencies of servers until profit losses exceed
    energy savings.

    """
    def reevaluate(self):
        self.schedule = Schedule()
        self._original_vm_hosts = {} # stores original VM allocations
        t = self.environment.get_time() # current time
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
            self._place(vm, host, t)

        # schedule frequency scaling
        #import ipdb; ipdb.set_trace()
        return self.schedule
