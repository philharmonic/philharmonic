"""generate artificial input"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta

from philharmonic import Machine, Server, VM, VMRequest, Cloud

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
    #print(mu, sigma)

    values = mu + sigma * np.random.randn(num)
    # negative to zero
    values[values<0]=0
    if ceil:
        values = np.ceil(values).astype(int)
    return values


# DC description
#---------------

def small_infrastructure():
    """return a list of Servers with determined resource capacities"""
    num_servers = 5
    Machine.resource_types = ['RAM', '#CPUs']
    RAM = [8]*num_servers
    numCPUs = [4]*num_servers
    servers = []
    for i in range(num_servers):
        if i < 3:
            location = 'A' # TODO: real codes
        else:
            location = 'B'
        s = Server(RAM[i], numCPUs[i], location=location)
        servers.append(s)
    return Cloud(servers=servers)

def peak_pauser_infrastructure():
    """1 server hosting 1 vm"""
    server = Server()
    vm = VM()
    cloud = Cloud([server], [vm])
    return cloud

# VM requests
#------------
# - global settings TODO: config file
VM_num = 3
# e.g. CPUs
min_cpu = 1
max_cpu = 2
min_ram = 1
max_ram = 2
# e.g. seconds
min_duration = 60 * 60 # 1 hour
max_duration = 60 * 60 * 3 # 3 hours
#max_duration = 60 * 60 * 24 * 10 # 10 days

def normal_vmreqs(start, end=None, round_to_hour=True):
    """Generate the VM creation and deletion events in.
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)

    """
    delta = end - start
    # array of VM sizes
    cpu_sizes = normal_population(VM_num, min_cpu, max_cpu)
    ram_sizes = normal_population(VM_num, min_ram, max_ram)
    # duration of VMs
    durations = normal_population(VM_num, min_duration, max_duration)
    requests = []
    moments = []
    for cpu_size, ram_size, duration in zip(cpu_sizes, ram_sizes, durations):
        vm = VM(ram_size, cpu_size)
        # the moment a VM is created
        offset = pd.offsets.Second(np.random.uniform(0., delta.total_seconds()))
        requests.append(VMRequest(vm, 'boot'))
        t = start + offset
        if round_to_hour:
            t = pd.Timestamp(t.date()) + pd.offsets.Hour(t.hour)
        moments.append(t)
        # the moment a VM is destroyed
        offset += pd.offsets.Second(duration)
        if start + offset <= end: # event is relevant
            requests.append(VMRequest(vm, 'delete'))
            moments.append(start + offset)
    events = pd.TimeSeries(data=requests, index=moments)
    return events.sort_index()

def no_requests(start, end):
    return pd.TimeSeries()

# time range (for the simulation)
#------------
def two_days():
    return pd.date_range('2013-02-25 00:00', periods=48, freq='H')

# geotemporal inputs
#------------

def simple_el():
    idx = two_days()
    halflen = len(idx)/2
    a = [0.05] * halflen + [0.13] * halflen
    b = [0.012] * halflen + [0.06] * halflen
    el_prices = pd.DataFrame({'A': a, 'B': b}, idx)
    return el_prices

def simple_temperature():
    idx = two_days()
    n = len(idx)
    a = 3 * n / 4 * [23] + n / 4 * [0.13]
    b = 3 * n / 4 * [-3] + n / 4 * [1]
    temperature = pd.DataFrame({'A': a, 'B': b}, idx)
    return temperature
