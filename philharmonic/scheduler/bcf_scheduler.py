from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration
from philharmonic import calculate_pue

def sort_vms_big_first(VMs):
    """Sort VMs by resource size - bigger first."""
    return sorted(VMs, key=lambda x : (x.res['#CPUs'], x.res['RAM']),
                  reverse=True)

def sort_active_pms(PMs, state, cost):
    """Sort by free capacity decreasing (fill out almost full servers first),
    by electricity price increasing (cheaper locations are preferred).
    Used for sorting active hosts to choose targets for new VMs.

    e.g. desired: (2 GB, $0.08), (4 GB, $0.04), (4 GB, $0.08)

    """

    # TODO: don't hardcode the resources
    return sorted(PMs,
                  key=lambda x : (state.free_cap[x]['#CPUs'],
                                  state.free_cap[x]['RAM'],
                                  cost[x.loc]))
def sort_inactive_pms(PMs, state, cost):
    """Sort by preferring bigger hosts, then by cost
    for waking up inactive hosts.

    e.g. desired: (4 GB, $0.04), (4 GB, $0.08), (2 GB, $0.08)

    """

    # TODO: don't hardcode the resources
    # TODO: check if cost more important in other scenarios
    return sorted(PMs,
                  key=lambda x : (-state.free_cap[x]['#CPUs'],
                                  -state.free_cap[x]['RAM'],
                                  cost[x.loc]))

class BCFScheduler(IScheduler):
    """Best Cost Fit (BCF) scheduling algorithm. Greedily places VMs on servers
    to favour locations with lower electricity and cooling costs and
    maximise utilisation.

    """

    def _fits(self, vm, server):
        """Returns the utilisation of adding vm to server
        or -1 in case some resource's capacity is exceeded.

        """
        # TODO: reuse free_cap data
        # TODO: this method should probably be a part of Cloud
        current = self.cloud.get_current()
        total_utilisation = 0.
        utilisations = {}
        for i in server.resource_types:
            used = 0.
            for existing_vm in current.alloc[server]:
                used += existing_vm.res[i]
            # add our own VM's resource demand
            used += vm.res[i]
            utilisations[i] = used/server.cap[i]
            if used > server.cap[i]: # capacity exceeded for this resource
                return -1
        uniform_weight = 1./len(server.resource_types)
        weights = {res : uniform_weight for res in server.resource_types}
        for resource_type, utilisation in utilisations.iteritems():
            total_utilisation += weights[resource_type] * utilisation
        return total_utilisation

    def _place(self, vm, host, t):
        """Place vm on host. A migration will be scheduled if necessary or
        nothing will be done if the vm is already there.

        """
        #TODO: the vm should be removed from the original server only here
        action = Migration(vm, host)
        self.cloud.apply(action)
        self.current = self.cloud.get_current()
        if (vm in self._original_vm_hosts and
            host == self._original_vm_hosts[vm]): # migration not necessary
            return
        self.schedule.add(action, t)

    def _remove_vms_from_underutilised_hosts(self):
        """mutable method that finds underutilised hosts, removes VMs from
        them in the current state, updates the _original_vm_hosts dictionary
        and returns all such VMs.

        """
        vms = []
        state = self.cloud.get_current()
        for s in self.cloud.servers:
            if state.underutilised(s):
                vms.extend(state.alloc[s])
                for vm in state.alloc[s]:
                    self._original_vm_hosts[vm] = s
                # remove the VMs from that host for now
                self.cloud.get_current().remove_all(s) # transition?
        return vms

    def find_host(self, vm):
        # TODO: this group of commands can be done only once for a list of VMs
        # in the current moment
        self.current = self.cloud.get_current()
        el, temp = self.environment.current_data()
        # take only current values - TODO: average over forecast window
        el = el.loc[self.environment.t]
        temp = temp.loc[self.environment.t]
        # combined cost based on el. price and temperature
        cost = el * calculate_pue(temp)
        all_hosts = self.cloud.servers
        hosts = filter(lambda s : not self.current.server_free(s), all_hosts)
        hosts = sort_active_pms(hosts, self.current, cost)
        inactive_hosts = filter(lambda s : self.current.server_free(s),
                                all_hosts)
        inactive_hosts = sort_inactive_pms(inactive_hosts, self.current, cost)

        mapped = False
        while not mapped:
            # sort for one of - first pass, free_cap changed or new host
            hosts = sort_active_pms(hosts, self.current, cost)
            for host in hosts:
                if self._fits(vm, host) != -1:
                    mapped = True
                    break
            if not mapped:
                if len(inactive_hosts) > 0: # activate an inactive host
                    host = inactive_hosts.pop(0)
                    hosts.append(host)
                else:
                    return None
        return host

    def reevaluate(self):
        self.schedule = Schedule()
        self._original_vm_hosts = {}
        t = self.environment.get_time()

        VMs = []
        # get VMs that need to be placed
        #  - VMs from boot requests
        requests = self.environment.get_requests()
        for request in requests:
            #import ipdb; ipdb.set_trace()
            if request.what == 'boot':
                VMs.append(request.vm)
        #  - select VMs on underutilised PMs
        VMs.extend(self._remove_vms_from_underutilised_hosts())
        # TODO: find and reallocate VMs from expensive locations
        VMs = sort_vms_big_first(VMs)
        if len(VMs) == 0:
            return self.schedule

        for vm in VMs:
            host = self.find_host(vm)
            if host is None:
                raise Exception("not enough free resources")
            self._place(vm, host, t)

        return self.schedule
