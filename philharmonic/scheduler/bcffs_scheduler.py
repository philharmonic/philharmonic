import copy

import pandas as pd
import numpy as np

from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.scheduler.bcf_scheduler import *
from philharmonic import Schedule, Migration, IncreaseFreq, DecreaseFreq
from philharmonic import conf
import evaluator as ev

def _nan_to_high(value):
    if np.isnan(value):
        return 999
    else:
        return value

def _empty_mean(array):
    """Sort or set to 999 for empty array."""
    if len(array) == 0:
        return 999
    else:
        return array.mean()

def sort_pms_by_beta(servers, state):
    """Sort servers by the average beta of vms assigned to them
    in @param state.

    """
    s_beta = {s: _empty_mean(np.array([vm.beta for vm in state.alloc[s]])) \
              for s in servers}
    sorted_servers = sorted(servers, key=lambda s : (s_beta[s]))
    return sorted_servers

class BCFFSScheduler(BCFScheduler):
    """Best Cost Fit Frequency Scaling (BCFFS) scheduling algorithm.
    In the first stage migrates VMs to servers maximising utilisation
    and favouring locations with lower electricity and cooling costs.
    In the second stage, when the maximum allowed rate of migrations is
    reached, scales the frequencies of servers until profit losses exceed
    energy savings.

    """

    # TODO: these two methods should be a part of the model,
    # as they touch too many model internals
    # (available to the scheduler)
    def _limit_cloud_to_server(self, server):
        """Temporarily consider only this server as the cloud, filter only
        actions and state properties for this server (for performance).

        """
        all_servers = self.cloud.servers
        self.cloud.servers = [server]
        self._all_servers = all_servers
        # preserve and limit state
        self._all_servers_real = self.cloud._real
        self.cloud._real = self.cloud._real.copy()
        self.cloud._real.limit_to_server(server)
        self.cloud.reset_to_real()

    def _restore_cloud_actions(self):
        """Reverse _limit_cloud_to_server."""
        # assemble the cloud and actions back
        self.cloud.servers = self._all_servers
        # restore state
        self.cloud._real = self._all_servers_real

    def _get_profit_and_cost(self):
        """Shorthand to calculate service profit and energy cost."""
        # - calculate profit
        profit = ev.calculate_service_profit(self.cloud, self.environment,
                                             self.freq_schedule,
                                             self.t, self.end)
        # - calculate energy cost
        en_cost = ev.combined_cost(self.cloud, self.environment,
                                   self.freq_schedule, self.el, self.temp,
                                   self.t, self.end,
                                   power_model=conf.power_model)
        return profit, en_cost

    def _add_freq_to_schedule(self, server):
        """Add the resulting frequency changes from the counter
        to the schedule.

        """
        if self._server_freq_change > 0:
            action = IncreaseFreq(server)
        else:
            action = DecreaseFreq(server)
            self._server_freq_change = -self._server_freq_change
        while self._server_freq_change > 0:
            self.schedule.add(action, self.t)
            self._server_freq_change -= 1

    def _increase_frequency(self, server):
        """Increase frequency and note it in the counter."""
        self.state.transition(IncreaseFreq(server), inplace=True)
        self.freq_schedule.add(IncreaseFreq(server), self.t)
        self._server_freq_change += 1

    def _decrease_frequency(self, server):
        """Decrease frequency and note it in the counter."""
        self.state.transition(DecreaseFreq(server), inplace=True)
        self.freq_schedule.add(DecreaseFreq(server), self.t)
        self._server_freq_change -= 1

    def _reset_to_max_frequency(self, server):
        """Add IncreaseFreq actions until the maximum frequency is reached."""
        while self.state.freq_scale[server] != conf.freq_scale_max:
            self._increase_frequency(server)

    def _schedule_frequency_scaling(self):
        """Add the frequency change actions to the schedule which result in
        energy savings higher than the profit losses incurred by
        performance-based pricing.

        """
        # TODO: implement simpler state checkpoints
        self._original_real = self.cloud._real # preserve original real
        # pretend the migrations were really applied
        self.cloud._real = self.cloud._current
        self.cloud.reset_to_real()
        # schedule of frequency changes for evaluation
        active_PMs = [s for s in self.cloud.servers \
                      if not self.cloud.get_current().server_free(s)]
        sorted_active_PMs = sort_pms_by_beta(active_PMs,
                                             self.cloud.get_current())
        for server in sorted_active_PMs:
            # we store freq. changes for the server in this temporary schedule
            self.freq_schedule = Schedule()
            self._limit_cloud_to_server(server)
            self.state = self.cloud.get_current() # for testing effects
            decrease_feasible = False
            self._server_freq_change = 0 # reset the counter of freq. changes
            self._reset_to_max_frequency(server)
            profit_previous, en_cost_previous = self._get_profit_and_cost()
            while True:
                self._decrease_frequency(server)
                # debug beta=1.0, en cost increase
                profit, en_cost = self._get_profit_and_cost()
                en_savings = en_cost_previous - en_cost
                profit_loss = profit_previous - profit
                if en_savings >= profit_loss: # change is beneficial
                    decrease_feasible = True # continue trying other servers
                    profit_previous, en_cost_previous = profit, en_cost
                else: # not profitable
                    # undo last decrease, break inner loop
                    self._increase_frequency(server)
                    break
                if self.state.freq_scale[server] == conf.freq_scale_min:
                    break # we reached the lowest frequency, break inner loop
            self._restore_cloud_actions()
            self._add_freq_to_schedule(server) # add actions to schedule
            if conf.freq_breaks_after_nonfeasible and not decrease_feasible:
                break # outer loop - as the servers are sorted by avg. beta
        # restore the real state
        self.cloud._real = self._original_real
        self.cloud.reset_to_real()

    def reevaluate(self):
        """Look at the current state of the Cloud and Environment
        and schedule new/different actions if necessary.

        @returns: a Schedule with a time series of actions

        """
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

        # stage 1: schedule migrations
        for vm in VMs:
            host = self.find_host(vm)
            if host is None:
                raise Exception("not enough free resources")
            self._place(vm, host, self.t)

        # stage 2: schedule frequency scaling
        self._schedule_frequency_scaling()

        return self.schedule
