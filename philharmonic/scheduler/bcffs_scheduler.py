from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler.bcf_scheduler import *
from philharmonic import Schedule, Migration, IncreaseFreq, DecreaseFreq
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

    def _get_profit_and_cost(self):
        # - calculate profit (loss)
        profit = ev.calculate_service_profit(self.cloud, self.environment,
                                             self.schedule, self.t, self.end)
        # - calculate energy cost (saving)
        en_cost = ev.combined_cost(self.cloud, self.environment, self.schedule,
                                   self.el, self.temp, self.t, self.end)
        return profit, en_cost

    def _increase_frequency(self, server):
        incr_freq = IncreaseFreq(server)
        self.cloud.apply(incr_freq, inplace=True)
        self.schedule.add(incr_freq)

    def _decrease_frequency(self, server):
        decr_freq = DecreaseFreq(server)
        self.cloud.apply(decr_freq, inplace=True)
        self.schedule.add(decr_freq)

    def _reset_to_max_frequency(self, server):
        state = self.cloud.get_current()
        while state.freq_scale[server] != conf.freq_scale_max:
            self._increase_frequency()

    def _schedule_frequency_scaling(self):
        # TODO:
        # - filter out empty PMs
        # - beginning - reset to f_ma
        # planned actions for servers
        self._planned_actions = {s: [] for s in self.cloud.servers}
        #cloud.get_current
        for server in self.cloud.servers:
            profit_initial, en_cost_initial = self._get_profit_and_cost() # for f_current
            state = self.cloud.get_current()
            #planned_actions = []
            while state.freq_scale[server] != conf.freq_scale_min:
                decr_freq = DecreaseFreq(server)
                self.cloud.apply(decr_freq, inplace=True)
                # debug beta=1.0, en cost increase
                profit, en_cost = self._get_profit_and_cost() # for f_current
                en_savings = en_cost_initial - en_cost
                profit_loss = profit_initial - profit
                if en_savings > profit_loss:
                    #planned_actions.append(decr_freq)
                    self.schedule.add(decr_freq, self.t)
                else:
                    self.cloud.apply(IncreaseFreq(server), inplace=True)
                    break # not profitable any more

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
