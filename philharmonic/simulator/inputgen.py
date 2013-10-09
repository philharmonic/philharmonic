"""generate artificial input"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta

from philharmonic.scheduler.generic.model import Machine, Server, VM

# Cummon functionality
#---------------------

def normal_population(num, bottom, top, ceil=True):
    """ Return array @ normal distribution.
    bottom, top are approx. min/max values.
    
    """
    half = (top - bottom)/2.0
    # we want 99% of the population to enter the [min,max] interval
    sigma = half/3.0
    mu = bottom + half
    print(mu, sigma)
    
    values = mu + sigma * np.random.randn(num)
    # negative to zero
    values[values<0]=0
    if ceil:
        values = np.ceil(values).astype(int)
    return values


# DC description
#---------------

def small_infrastructure():
    num_servers = 3
    Machine.resource_types = ['RAM', '#CPUs']
    RAM = [4]*num_servers
    numCPUs = [2]*num_servers
    servers = []
    for i in range(num_servers):
        s = Server(RAM[i], numCPUs[i])
        servers.append(s)
    return servers


# VM requests
#------------
# - global settings TODO: config file
VM_num = 7
# e.g. CPUs
min_size = 1
max_size = 8
# e.g. seconds
min_duration = 60 * 60 # 1 hour
max_duration = 60 * 60 * 3 # 3 hours
#max_duration = 60 * 60 * 24 * 10 # 10 days

class VMEvent():
    """Container for VM creation/deletion events."""
    def __init__(self, vm, t, what):
        self.vm = vm
        self.t = t
        self.what = what
    def __str__(self):
        return "{2} {0} @{1}".format(self.vm, self.t, self.what)
    def __repr__(self):
        return self.__str__()

def normal_vmreqs(start, end=None):
    """Generate the VM creation and deletion events in. 
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)
    """
    delta = end - start
    # array of VM sizes
    sizes = normal_population(VM_num, min_size, max_size)
    # duration of VMs
    durations = normal_population(VM_num, min_duration, max_duration)
    events = []
    for size, duration in zip(sizes, durations):
        vm = VM(size)
        # the moment a VM is created
        offset = pd.offsets.Second(np.random.uniform(0., delta.total_seconds()))
        events.append(VMEvent(vm, start + offset, 'boot'))
        # the moment a VM is destroyed
        offset += pd.offsets.Second(duration)
        if start + offset <= end: # event is relevant
            events.append(VMEvent(vm, start + offset, 'delete'))
    return events
