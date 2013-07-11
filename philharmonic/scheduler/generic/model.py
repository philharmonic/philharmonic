'''
Created on Jul 11, 2013

@author: kermit
'''

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