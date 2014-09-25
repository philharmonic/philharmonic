from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic import Schedule, Migration

def sort_vms_decreasing(VMs):
    return sorted(VMs, key=lambda x : (x.res['#CPUs'], x.res['RAM']),
                  reverse=True)

def sort_pms_increasing(PMs, state):
    return sorted(PMs,
                  key=lambda x : (state.free_cap[x]['#CPUs'],
                                  state.free_cap[x]['RAM']))

class BFDScheduler(IScheduler):
    """Best fit decreasing (BFD) scheduler, as proposed for
    [OpenStack Neat](http://openstack-neat.org/).

    """

    def __init__(self, cloud=None, driver=None):
        IScheduler.__init__(self, cloud, driver)
        self._original_vm_hosts = {}

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
        if (vm in self._original_vm_hosts and
            host == self._original_vm_hosts[vm]): # migration not necessary
            return
        self.schedule.add(action, t)

    # TODO: maybe split into multiple functions and make this one immutable
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

    def reevaluate(self):
        self.schedule = Schedule()
        self._original_vm_hosts = {}
        t = self.environment.get_time()

        VMs = []
        # get VMs that need to be placed
        #  - VMs from boot requests
        requests = self.environment.get_requests()
        for request in requests:
            if request.what == 'boot':
                VMs.append(request.vm)
        #  - select VMs on underutilised PMs
        VMs.extend(self._remove_vms_from_underutilised_hosts())

        VMs = sort_vms_decreasing(VMs)

        if len(VMs) == 0:
            return self.schedule

        current = self.cloud.get_current()
        all_hosts = self.cloud.servers
        hosts = filter(lambda s : not current.server_free(s), all_hosts)
        hosts = sort_pms_increasing(hosts, current)
        inactive_hosts = filter(lambda s : current.server_free(s), all_hosts)
        inactive_hosts = sort_pms_increasing(inactive_hosts, current)

        for vm in VMs:
            mapped = False
            while not mapped:
                for host in hosts:
                    if self._fits(vm, host) != -1:
                        self._place(vm, host, t)
                        mapped = True
                        break
                if not mapped:
                    if len(inactive_hosts) > 0:
                        host = inactive_hosts.pop(0)
                        hosts.append(host)
                        hosts = sort_pms_increasing(hosts, current)
                    else:
                        break

        return self.schedule
