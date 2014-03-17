"""generate artificial input"""

import random
import pickle

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

def small_infrastructure(locations = ['A', 'B']):
    """return a list of Servers with determined resource capacities"""
    num_servers = 5
    Machine.resource_types = ['RAM', '#CPUs']
    RAM = [8]*num_servers
    numCPUs = [4]*num_servers
    servers = []
    for i in range(num_servers):
        if i < 3:
            location = locations[0]
        else:
            location = locations[1]
        s = Server(RAM[i], numCPUs[i], location=location)
        servers.append(s)
    return Cloud(servers=servers)

def peak_pauser_infrastructure():
    """1 server hosting 1 vm"""
    server = Server()
    vm = VM()
    cloud = Cloud([server], set([vm]))
    return cloud

# cloud's servers
server_num = 5
min_server_cpu = 4
max_server_cpu = 8
#locations

def normal_infrastructure(locations=['A', 'B'],
                          round_to_hour=True):
    """Generate the cloud's servers with random specs and
    uniformly distributed over all the locations

    """
    # array of server sizes
    cpu_sizes = normal_population(server_num, min_server_cpu,
                                  max_server_cpu)
    ram_sizes = normal_population(server_num, min_server_cpu,
                                  max_server_cpu)

    servers = []
    for cpu_size, ram_size in zip(cpu_sizes, ram_sizes):
        location = random.sample(locations, 1)[0]
        server = Server(ram_size, cpu_size, location=location)
        servers.append(server)
    return Cloud(servers=servers)

# VM requests
#------------
# - global settings TODO: config file
# VM requests
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

def normal_vmreqs(start, end, round_to_hour=True):
    """Generate the VM creation and deletion events in.
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)

    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
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
            t = start + offset
            if round_to_hour:
                t = pd.Timestamp(t.date()) + pd.offsets.Hour(t.hour)
            moments.append(t)
    events = pd.TimeSeries(data=requests, index=moments)
    return events.sort_index()

def simple_vmreqs(start='2013-02-25 00:00', end='2013-02-27 00:00'):
    """Generate the VM creation and deletion events in.
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)

    """
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")

    # environment
    times = pd.date_range(start, periods=48, freq='H')
    t1 = pd.Timestamp(start)
    t2 = pd.Timestamp(start)
    t3 = pd.Timestamp(start) + pd.offsets.Hour(3)
    t4 = pd.Timestamp(start) + pd.offsets.Hour(6)

    requests = [VMRequest(vm1, 'boot'), VMRequest(vm2, 'boot'),
                VMRequest(vm2, 'delete'), VMRequest(vm1, 'delete')]
    moments = [t1, t2, t3, t4]
    events = pd.TimeSeries(data=requests, index=moments)
    return events

def medium_vmreqs(start='2013-02-25 00:00', end='2013-02-27 00:00'):
    """Generate the VM creation and deletion events in.
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)

    """
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")

    # environment
    times = pd.date_range(start, periods=48, freq='H')
    t1 = pd.Timestamp(start)
    t2 = pd.Timestamp(start) + pd.offsets.Hour(1)
    t3 = pd.Timestamp(start) + pd.offsets.Hour(46)
    t4 = pd.Timestamp(start) + pd.offsets.Hour(47)

    requests = [VMRequest(vm1, 'boot'), VMRequest(vm2, 'boot'),
                VMRequest(vm2, 'delete'), VMRequest(vm1, 'delete')]
    moments = [t1, t2, t3, t4]
    events = pd.TimeSeries(data=requests, index=moments)
    return events

def no_requests(start, end):
    return pd.TimeSeries()

# time range (for the simulation)
#------------
def two_days(start=None):
    if start is None:
        start = '2013-02-25 00:00'
    return pd.date_range(start, periods=48, freq='H')

def two_hours(start=None):
    if start is None:
        start = '2013-02-25 00:00'
    return pd.date_range(start, periods=2, freq='H')

# geotemporal inputs
#------------

def simple_el(start=None):
    idx = two_days(start)
    halflen = len(idx)/2
    a = [0.05] * halflen + [0.13] * halflen
    b = [0.012] * halflen + [0.06] * halflen
    el_prices = pd.DataFrame({'A': a, 'B': b}, idx)
    return el_prices

def medium_el(start=None):
    """A and B 'switch sides'"""
    idx = two_days(start)
    halflen = len(idx)/2
    a = [0.05] * halflen + [0.013] * halflen
    b = [0.012] * halflen + [0.06] * halflen
    el_prices = pd.DataFrame({'A': a, 'B': b}, idx)
    return el_prices

def simple_temperature(start=None):
    idx = two_days(start)
    n = len(idx)
    a = 3 * n / 4 * [23] + n / 4 * [0.13]
    b = 3 * n / 4 * [-3] + n / 4 * [1]
    temperature = pd.DataFrame({'A': a, 'B': b}, idx)
    return temperature

def medium_temperature(start=None):
    idx = two_days(start)
    n = len(idx)
    a = 3 * n / 4 * [23] + n / 4 * [4]
    b = 3 * n / 4 * [-3] + n / 4 * [19]
    temperature = pd.DataFrame({'A': a, 'B': b}, idx)
    return temperature


# USA data
#-----------
import os
DATA_LOC = os.path.expanduser('~/Dropbox/dev/skripte/python/notebook')
DATA_LOC = os.path.join(DATA_LOC, 'data/geotemporal')

def usa_el(start=None):
    el_prices = pd.read_csv(os.path.join(DATA_LOC, 'prices.csv'),
                            index_col=0, parse_dates=[0])
    return el_prices

def usa_temperature(start=None):
    temperature = pd.read_csv(os.path.join(DATA_LOC, 'temperatures.csv'),
                              index_col=0, parse_dates=[0])
    return temperature

def usa_small_infrastructure():
    return small_infrastructure(['MI-Detroit', 'IN-Indianapolis'])

def usa_two_days():
    return two_days('2010-01-01 00:00')

def usa_two_hours():
    return two_hours('2010-01-01 00:00')

def usa_whole_period():
    temperature = usa_temperature()
    start, end = temperature.index[0], temperature.index[-26]
    return pd.date_range(start, end, freq='H')

def generate_fixed_input():
    from philharmonic import conf
    # override module settings with the config file
    for key, value in conf.inputgen_settings.iteritems():
        globals()[key] = value
    temperature = usa_temperature()
    #start, end = temperature.index[0], temperature.index[-26]
    factory = conf.get_factory()
    start, end = factory['times']()[[0, -1]]
    locations = temperature.columns.values
    servers = normal_infrastructure(locations)
    requests = normal_vmreqs(start, end)
    with open('servers.pkl', 'w') as pkl_srv:
        pickle.dump(servers, pkl_srv)
    with open('requests.pkl', 'w') as pkl_req:
        pickle.dump(requests, pkl_req)
    print(servers, requests)

def servers_from_pickle():
    with open('servers.pkl') as pkl_srv:
        return pickle.load(pkl_srv)

def requests_from_pickle(*args, **kwargs): # TODO: don't need input
    with open('requests.pkl') as pkl_req:
        return pickle.load(pkl_req)

if __name__ == '__main__':
    generate_fixed_input()
