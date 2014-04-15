'''
The cloud model as seen from the cloud provider's perspective.

Created on Jul 11, 2013

@author: kermit

'''
import copy
import itertools

from philharmonic.utils import deprecated

def format_spec(spec):
    s = "{"
    for key, value in spec.iteritems():
        s += "{0}:{1}, ".format(key, value)
    s = s[:-2]
    s += "}"
    return s

# some non-semantic functionality common for VMs and servers
class Machine(object):
    resource_types = ['RAM', '#CPUs'] # to be overridden with actual values
    def __init__(self, *args):
        self.id = type(self)._new_id()
        self.spec = {}
        for (i, arg) in enumerate(args):
            self.spec[self.resource_types[i]] = arg

    def __str__(self):
        # return "({2}:{0}:{1})".format(str(id(self))[-3:],
        #                               format_spec(self.spec),
        #                               self.machine_type)
        return self.__repr__()
    def __repr__(self):
        return "{}:{}".format(self.machine_type, str(self.id))
    def __eq__(self, other):
        return (self.id, self.machine_type) == (other.id, other.machine_type)
    def __hash__(self):
        return hash((self.id, self.machine_type))

def _delegate_to_obj(obj, method_name, *args):
    method = getattr(obj, method_name)
    method(*args)


# the model
# ==========

class VM(Machine):

    machine_type = 'VM'
    _new_id = itertools.count(start=1).next

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
    """A physical server."""

    machine_type = 'PM'
    _new_id = itertools.count(start=1).next

    def __init__(self, *args, **kwargs):
        """@param location: server's geographical location"""
        super(Server, self).__init__(*args)
        self.cap = self.spec
        if 'location' in kwargs:
            self._loc = kwargs['location']

    def get_location(self):
        return self._loc

    def set_location(self, location):
        self._loc = location

    location = property(get_location, set_location, doc="geographical location")
    loc = property(get_location, set_location, doc="geographical location")

    def __repr__(self):
        s = "{}:{}".format(self.machine_type, str(self.id))
        try:
            s += '@{}'.format(self.location)
        except AttributeError:
            pass
        return s

# Schedule
# ==========

class State():
    """the state of the cloud at a single moment. Various methods like migrate,
    pause... for changing it."""

    @staticmethod
    def random():
        """create a random state"""
        return State([Server(2,2), Server(4,4)], [VM(1,1), VM(1,1)])

    def __init__(self, servers=[], vms=set(), auto_allocate=False):
        self.servers = servers
        self.vms = vms
        self.alloc = {} # servers -> allocated machines
        self.paused = set() # those VMs that are paused
        self.suspended = set() # those VMs that are paused
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
        """change current state to have vm on server s"""
        self.alloc[s].add(vm)

    def remove(self, vm, s):
        """change current state to not have vm on server s"""
        self.alloc[s].remove(vm)

    # action effects (consequence of applying Action to State)
    #---------------

    def migrate(self, vm, s):
        """change current state to have vm in s instead of the old location"""
        for server, vms in self.alloc.iteritems():
            if vm in vms:
                if server == s:
                    # it's already there
                    return
                else: # VM was elsewhere - removing
                    # remove from old server
                    vms.remove(vm)
        # add it to the new one
        if s is not None: # if s is None, vm is being deleted
            self.alloc[s].add(vm)
        # TODO: faster reverse-dictionary lookup
        # http://stackoverflow.com/a/2569076/544059

    def pause(self, vm):
        self.paused.add(vm) # add to paused set

    def unpause(self, vm):
        self.paused.remove(vm) # remove from paused set

    def boot(self, vm):
        """a VM is requested by the user, but is not yet allocated"""
        self.vms.add(vm)

    def delete(self, vm):
        """user requested for a vm to be deleted"""
        try:
            self.vms.remove(vm)
        except KeyError: # the VM wasn't even there (booted outside environment)
            pass
        self.migrate(vm, None) # remove vm from its host server

    #---------------

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

    def transition(self, action):
        """transition into new state acccording to action"""
        new_state = self.copy()
        #new_state.migrate(migration.vm, migration.server)
        apply_effect = getattr(new_state, action.name)
        apply_effect(*action.args)
        return new_state

    def calculate_utilisations(self):
        self.utilisations = {}
        uniform_weight = 1./len(Server.resource_types)
        weights = {res : uniform_weight for res in Server.resource_types}
        for server in self.servers:
            total_utilisation = 0.
            utilisations = {}
            for i in server.resource_types:
                used = 0.
                for vm in self.alloc[server]:
                    used += vm.res[i]
                utilisations[i] = used/server.cap[i]
                if utilisations[i] > 1:
                    utilisations[i] = 1
            for resource_type, utilisation in utilisations.iteritems():
                total_utilisation += weights[resource_type] * utilisation
            self.utilisations[server] = total_utilisation
        return self.utilisations

    # constraint checking
    # C1
    def is_allocated(self, vm):
        for s in self.servers:
            if vm in self.alloc[s]:
                return True
        return False

    def allocation(self, vm):
        for s in self.servers:
            if vm in self.alloc[s]:
                return s
        return None

    def all_allocated(self):
        to_check = set(copy.copy(self.vms))
        for s in self.servers:
            to_check = to_check.difference(self.alloc[s])
        return len(to_check) == 0

    def ratio_allocated(self):
        to_check = set(copy.copy(self.vms))
        total = len(to_check)
        if total == 0:
            return 1.0
        for s in self.servers:
            to_check = to_check.difference(self.alloc[s])
        allocated = total - len(to_check)
        ratio = float(allocated) / total
        return ratio

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

    def capacity_penalty(self):
        max_overcap = {res: 0. for res in Machine.resource_types}
        ratio_overcap = {res: 0. for res in Machine.resource_types}
        for s in self.servers:
            for r in Machine.resource_types:
                used = 0
                for vm in self.alloc[s]:
                    used += vm.res[r]
                overcap = used - s.cap[r]
                if overcap > max_overcap[r]:
                    max_overcap[r] = overcap
                    ratio_overcap[r] = float(overcap) / s.cap[r]
        penalty = pd.Series(ratio_overcap).mean()
        if penalty > 1.:
            penalty = 1.
        return penalty

    def ratio_within_capacity(self): # TODO: by resource overflows
        """ratio of servers that are within capacity"""
        num_ok = 0
        for s in self.servers:
            if self.within_capacity(s):
                num_ok += 1
        if len(self.servers) == 0:
            return 1.0
        ratio = float(num_ok) / len(self.servers)
        return ratio

class Action(object):
    """A static representation of an action on the cloud."""
    name = ''
    args = None
    def __repr__(self):
        return '{0}: {1}'.format(self.name, str(self.args))
    def __str__(self):
        return self.__repr__()

class Migration(Action):
    """migrate vm to server"""
    def __init__(self, vm, server):
        self.vm = vm
        self.server = server
        self.args = [vm, server]
    name = 'migrate'
    def __repr__(self):
        return '{} -> {}'.format(str(self.vm), str(self.server))

class Pause(Action):
    """pause vm"""
    def __init__(self, vm):
        self.args = [vm]
    name = 'pause'

class Unpause(Action):
    """pause vm"""
    def __init__(self, vm):
        self.args = [vm]
    name = 'unpause'

class VMRequest(Action):
    """VM creation/deletion actions."""
    def __init__(self, vm, what):
        self.vm = vm
        self.args = [vm]
        self.what = what
        self.name = self.what
    def __str__(self):
        return "{0} {1}".format(self.what, self.vm)
    def __repr__(self):
        return self.__str__()

import pandas as pd
class Schedule(object):
    """(initial state? - part of Cloud) and a time series of actions"""
    def __init__(self):
        self.actions = pd.TimeSeries()
        self.actions.name = 'actions'

    def add(self, action, t):
        try:
            existing_actions = self.filter_current_actions(
                t, self.environment.period)
        except AttributeError:
            pass
        else:
            for t_ex, existing in existing_actions.iteritems():
                if existing.name == action.name and existing.vm == action.vm:
                    self.actions = self.actions[self.actions != existing]
        new_action = pd.Series({t: action})
        self.actions = pd.concat([self.actions, new_action])
        self.actions.name = 'actions'
        self.actions = self.actions.sort_index()

    def filter_current_actions(self, t, period):
        """return time series of actions in interval
        (closed on the left, open on the right)

        """
        justabit = pd.offsets.Micro(1)
        return self.actions.ix[t:t + period - justabit]
        #return self.actions[t:t + period - justabit]

    def __repr__(self):
        return self.actions.__repr__()

    def __str__(self):
        return self.actions.__str__()

# Cloud
# ==========

class Cloud():
    """Contains all the VMs and servers and keeps current/future/past states.
    Does not perform real actions by itself, but serves as a placeholder
    for experimenting with and evaluating actions by the Scheduler.

    The IManager can then use the real state and the Schedule to
    perform actual actions.

    States:
    - _initial - at the very beginning (probably no VMs allocated)
    - _real - reflects the actual physical allocations
              (as of the last action applied by the manager)
    - _current - _real or some later virtual state - controlled by the Scheduler

    Workflow:
    - action on Cloud -> create Action instance -> add to Schedule

    """
    def __init__(self, servers, initial_vms=set(), auto_allocate=False):
        self._servers = servers
        self._initial = State(servers, set(initial_vms), auto_allocate)
        for machine in servers + list(initial_vms): # know thy parent
            machine.cloud = self
        self._real = self._initial
        self.reset_to_real()

    def reset_to_real(self):
        """Set the current state back to what the real state of the cloud is."""
        self._current = self._real

    def reset_to_initial(self):
        """Set the current state back to the initial state."""
        self._current = self._initial

    def get_vms(self):
        """return the VMs in the current state"""
        return self._current.vms

    def get_servers(self):
        return self._servers

    def get_current(self):
        """Get the current state."""
        return self._current

    vms = property(get_vms, doc="get the VMs in the current state")
    servers = property(get_servers, doc="get the servers (always the same)")

    def apply(self, action):
        """Apply an Action on the current state."""
        self._current = self._current.transition(action)

    def apply_real(self, action):
        """Apply an Action on the real state (reflecting the actual physical
        state) and reset the virtual state.

        """
        self._real = self._real.transition(action)
        self.reset_to_real()

    @deprecated
    def connect(self):
        """Establish a connection with the driver
        Deprecated - the manager should apply actions, not the Cloud model."""
        self.driver.connect()

    #TODO: do we really want methods here as well? Action instances better?
    def pause(self, *args):
        _delegate_to_obj(self._current, self.pause.__name__, *args)

    def unpause(self, *args):
        _delegate_to_obj(self._current, self.unpause.__name__, *args)

#TODO: separate model for planning actions (state, transition etc.)
# and model for really executing actions

#TODO: maybe split into several files
# - model
# - schedule
# (- cloud)
