from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration

def sort_vms_big_first(VMs):
    """Sort VMs by resource size - bigger first."""
    return sorted(VMs, key=lambda x : (x.res['#CPUs'], x.res['RAM']),
                  reverse=True)

def sort_pms_best_first(PMs, state, el):
    """Sort by free capacity decreasing (fill out almost full servers first),
    by electricity price increasing (cheaper locations are preferred).

    """

    # TODO: add cooling efficiency
    # TODO: don't hardcode the resources
    return sorted(PMs,
                  key=lambda x : (-state.free_cap[x]['#CPUs'],
                                  -state.free_cap[x]['RAM'],
                                  el[x.loc]))
def sort_pms_cost_first(PMs, state, el):
    """Sort by cost first, then prefer larger hosts
    (for waking up inactive hosts).

    """

    # TODO: add cooling efficiency
    # TODO: don't hardcode the resources
    return sorted(PMs,
                  key=lambda x : (el[x.loc],
                                  -state.free_cap[x]['#CPUs'],
                                  -state.free_cap[x]['RAM']))

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
        # TODO: find and reallocate VMs from expensive locations
        #VMs.extend(self._remove_vms_from_underutilised_hosts())

        VMs = sort_vms_big_first(VMs)

        if len(VMs) == 0:
            return self.schedule

        self.current = self.cloud.get_current()
        el, temp = self.environment.current_data()
        # take only current values - TODO: average over forecast window
        el = el.loc[self.environment.t]
        temp = temp.loc[self.environment.t]
        all_hosts = self.cloud.servers
        hosts = filter(lambda s : not self.current.server_free(s), all_hosts)
        hosts = sort_pms_best_first(hosts, self.current, el)
        inactive_hosts = filter(lambda s : self.current.server_free(s),
                                all_hosts)
        inactive_hosts = sort_pms_cost_first(inactive_hosts, self.current, el)

        for vm in VMs:
            mapped = False
            while not mapped:
                # sort for one of - first pass, free_cap changed or new host
                hosts = sort_pms_best_first(hosts, self.current, el)
                for host in hosts:
                    if self._fits(vm, host) != -1:
                        self._place(vm, host, t)
                        mapped = True
                        break
                if not mapped:
                    if len(inactive_hosts) > 0: # activate an inactive host
                        host = inactive_hosts.pop(0)
                        hosts.append(host)
                    else:
                        break

        return self.schedule
