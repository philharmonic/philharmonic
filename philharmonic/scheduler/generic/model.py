'''
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
        return str(self.spec)
    def __repr__(self):
        return str(self.spec)

# the model
class VM(Machine):
    
    def __init__(self, *args):
        super(VM, self).__init__(*args)
        self.res = self.spec

class Server(Machine):
    def __init__(self, *args):
        super(Server, self).__init__(*args)
        self.cap = self.spec
        self.alloc = set()
        
    def migrate(self, vm, s):
        try:
            self.alloc.remove(vm)
            s.alloc.add(vm)
        except ValueError:
            print('VM not here')
            raise

# constraint checking
# C1
def is_allocated(servers, vm):
    for s in servers:
        if vm in s.alloc:
            return True
    return False

def all_allocated(servers, VMs):
    for vm in VMs:
        if not is_allocated(servers, vm):
            return False
    return True

#C2
def within_capacity(s):
    for i in s.resource_types:
        used = 0
        for vm in s.alloc:
            used += vm.res[i]
        #print('%d vs %d' % (used, s.cap[i]))
        if used > s.cap[i]:
            return False
    return True

def all_within_capacity(servers):
    for s in servers:
        if not within_capacity(s):
            return False
    return True

# Schedule
# ==========

class State():
    """the state of the cloud at a single moment"""
    def __init__(self, servers=None, VMs=None):
        self.servers = servers
        self.VMs = VMs
        
    def __deepcopy__(self, memo):
        new_state = State()
        new_state.__dict__.update(self.__dict__)
        new_state.servers = []
        new_state.VMs = []
        for s in self.servers:
            new_server = copy.copy(s)
            # we keep the original vm objects!
            new_server.alloc = set()
            for vm in s.alloc:
                new_state.VMs.append(vm)
                new_server.alloc.add(vm)
            new_state.servers.append(new_server)
        return new_state
             
    
    def __repr__(self):
        return '%s , %s' % (self.servers.__repr__(), self.VMs.__repr__())
        
    def transition(self, migration):
        """transition acccording to migration"""
        new_state = copy.deepcopy(self)
        new_state

        
class Migration():
    """ migrate vm to server """
    def __init__(self, vm, server):
        self.vm = vm
        self.server = server
        
class Schedule():
    """initial state and a time series of migrations"""
    pass