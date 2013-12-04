'''
The cloud model as seen from the cloud provider's perspective.

Created on Jul 11, 2013

@author: kermit

'''
import copy

# some non-semantic functionality common for VMs and servers
class Machine(object):
    resource_types = ['RAM', '#CPUs'] # to be overridden with actual values

    def __init__(self, *args):
        self.spec = {}
        for (i, arg) in enumerate(args):
            self.spec[self.resource_types[i]] = arg

    def __str__(self):
        return "<id:{0}, spec:{1}>".format(str(id(self))[-3:], str(self.spec))
    def __repr__(self):
        return str(self)

def _delegate_to_obj(obj, method_name, *args):
    method = getattr(obj, method_name)
    method(*args)


# the model
# ==========

class VM(Machine):

    def __init__(self, *args):
        super(VM, self).__init__(*args)
        self.res = self.spec

    # calling (un)pause or migrate on a VM gets routed to the cloud
    # and then to the current state

    #TODO: create these methods automatically
    def pause(self):
        _delegate_to_obj(self.cloud, self.pause.__name__, self)

    def unpause(self):
        _delegate_to_obj(self.cloud, self.unpause.__name__, self)

    def migrate(self, server):
        _delegate_to_obj(self.cloud, self.pause.__name__, self, server)

class Server(Machine):
    def __init__(self, *args):
        super(Server, self).__init__(*args)
        self.cap = self.spec

class VMRequest():
    """Container for VM creation/deletion events."""
    def __init__(self, vm, what):
        self.vm = vm
        self.what = what
    def __str__(self):
        return "{0} {1}".format(self.what, self.vm)
    def __repr__(self):
        return self.__str__()

# Schedule
# ==========

class State():
    """the state of the cloud at a single moment"""

    @staticmethod
    def random():
        """create a random state"""
        return State([Server(2,2), Server(4,4)], [VM(1,1), VM(1,1)])

    def __init__(self, servers=[], vms=[], auto_allocate=True):
        self.servers = servers
        self.vms = vms
        self.alloc = {} # servers -> allocated machines
        # TODO: paused, suspended
        for s in self.servers:
            self.alloc[s] = set()
        if auto_allocate:
            self.auto_allocate()

    def __repr__(self):
        rep = ''
        for s in self.servers:
            s_rep = '%s -> %s;\n' % (s.__repr__(), self.alloc[s].__repr__())
            rep += s_rep
        return rep

    def auto_allocate(self):
        """place all VMs on the first server"""
        for vm in self.vms:
            self.place(vm, self.servers[0])


    def place(self, vm, s):
        """change current state to have vm in s"""
        self.alloc[s].add(vm)

    def remove(self, vm, s):
        """change current state to not have vm in s"""
        self.alloc[s].remove(vm)

    def migrate(self, vm, s):
        """change current state to have vm in s instead of the old location"""
        for server, vms in self.alloc.iteritems():
            if vm in vms:
                if server == s:
                    # it's already there
                    return
                else:
                    # remove from old server
                    vms.remove(vm)
                    # add to the new one
                    self.alloc[s].add(vm)
        # TODO: faster reverse-dictionary lookup
        # http://stackoverflow.com/a/2569076/544059

    def pause(self, vm):
        pass # TODO: add to paused set

    def unpause(self, vm):
        pass # TODO: remove from paused set


    def copy(self):
        """ return a copy of the state with a new alloc instance"""
        new_state = State()
        #new_state.__dict__.update(self.__dict__)
        new_state.servers = self.servers
        new_state.vms = self.vms
        new_state.alloc = {}
        for s, vms in self.alloc.iteritems():
            new_state.alloc[s] = set(vms) # create a new set
        #TODO: copy.copy - probably faster
        return new_state

    def transition(self, migration):
        """transition acccording to migration"""
        new_state = self.copy()
        new_state.migrate(migration.vm, migration.server)
        return new_state

    # constraint checking
    # C1
    def is_allocated(self, vm):
        for s in self.servers:
            if vm in self.alloc[s]:
                return True
        return False

    def all_allocated(self):
        to_check = set(copy.copy(self.vms))
        for s in self.servers:
            to_check = to_check.difference(self.alloc[s])
        return len(to_check) == 0

    #C2
    def within_capacity(self, s):
        for i in s.resource_types:
            used = 0
            for vm in self.alloc[s]:
                used += vm.res[i]
            #print('%d vs %d' % (used, s.cap[i]))
            if used > s.cap[i]:
                return False
        return True

    def all_within_capacity(self):
        for s in self.servers:
            if not self.within_capacity(s):
                return False
        return True

class Migration():
    """ migrate vm to server """
    def __init__(self, vm, server):
        self.vm = vm
        self.server = server

    def __repr__(self):
        return '%s -> %s' % (self.vm, self.server)

class Schedule():
    """initial state and a time series of migrations"""
    pass


# Cloud
# ==========

class Cloud():
    """contains all the VMs and servers and keeps the current and past states"""
    def __init__(self, servers, initial_vms, auto_allocate=True):
        self._servers = servers
        self._initial = State(servers, initial_vms, auto_allocate)
        for machine in servers + initial_vms: # know thy parent
            machine.cloud = self
        self._current = self._initial

    def get_vms(self):
        return self._current.vms

    def get_servers(self):
        return self._servers

    vms = property(get_vms, doc="get the VMs in the current state")
    servers = property(get_servers, doc="get the servers (always the same)")

    def pause(self, *args):
        _delegate_to_obj(self._current, self.pause.__name__, *args)

    def unpause(self, *args):
        _delegate_to_obj(self._current, self.unpause.__name__, *args)

