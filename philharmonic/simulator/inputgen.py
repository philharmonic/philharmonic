"""generate artificial input"""

import random
import pickle
import math

import pandas as pd
import numpy as np
from scipy import stats
import scipy.stats
from datetime import timedelta

from philharmonic import conf
from philharmonic import Machine, Server, VM, VMRequest, Cloud
from philharmonic.utils import common_loc
from philharmonic.logger import *

# Cummon functionality
#---------------------

def synthetic_beta_population(output_size, input_beta_data):
    distribution = scipy.stats.expon
    model = distribution.fit(input_beta_data)#['mean'])
    # rvs generates random variates
    beta = distribution.rvs(size=output_size, *model)
    return beta

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

def normal_sample(bottom, top, ceil=True):
    """ Return a single sample from a normal distribution.
    bottom, top are approx. min/max values.

    """
    return normal_population(1, bottom, top, ceil)[0]

def distribution_population(num, bottom, top, ceil=True, distribution='normal'):
    """ Draw array from @param distribution.
    bottom, top are approx. min/max values.

    """
    if distribution == 'normal':
        return normal_population(num, bottom, top, ceil)
    elif distribution == 'uniform':
        if ceil:
            return np.random.randint(bottom, top + 1, num)
        else:
            return np.random.uniform(bottom, top, num)

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
min_server_ram = 4
max_server_ram = 8
#locations

def normal_infrastructure(locations=['A', 'B'],
                          round_to_hour=True):
    """Generate the cloud's servers with random specs and
    uniformly or normally distributed over all the locations

    """
    # array of server sizes
    cpu_sizes = distribution_population(
        server_num, min_server_cpu, max_server_cpu,
        distribution=resource_distribution)
    ram_sizes = distribution_population(
        server_num, min_server_ram, max_server_ram,
        distribution=resource_distribution)

    servers = []
    for cpu_size, ram_size in zip(cpu_sizes, ram_sizes):
        location = random.sample(locations, 1)[0] # return a random sample from all locations
        server = Server(ram_size, cpu_size, location=location)
        servers.append(server)
    return Cloud(servers=servers)

# VM requests
#------------
# simulate how users will use our cloud

# - global settings, **overriden** by the config.inputgen dictionary
# general stuff
# - the statistical distribution to draw resources and duration from
resource_distribution = 'normal'

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
beta_option = 1
max_cloud_usage = 0.8

def within_cloud_capacity(cloud_capacity, requested_capacity, max_cloud_usage):
    """Iterate through each resource and its (total) capacity"""
    for res, capacity in cloud_capacity.items():
        if requested_capacity[res] > capacity * max_cloud_usage:
            return False
    return True

def auto_vmreqs(start, end, round_to_hour=True,
                servers=[], **kwargs):
    """Generate VMRequests s.t. the requested resources do not exceed
    (on the average) max_cloud_usage of the available cloud capacity.

    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    delta = end - start
    avg_cap = lambda res : np.mean([server.cap[res] for server in servers])
    n = len(servers)
    cloud_capacity = {res : n*avg_cap(res) for res in servers[0].resource_types}
    requested_capacity = {res : 0. for res in servers[0].resource_types}
    requests = []
    moments = []
    while within_cloud_capacity(cloud_capacity, requested_capacity,
                                max_cloud_usage):
        cpu_size = distribution_population(
            1, min_cpu, max_cpu, distribution=resource_distribution)[0]
        ram_size = distribution_population(
            1, min_ram, max_ram, distribution=resource_distribution)[0]
        duration = distribution_population(
            1, min_duration, max_duration,
            distribution=resource_distribution)[0]

        vm = VM(ram_size, cpu_size)
        for r in vm.resource_types: # add the extra capacity for stop condition
            requested_capacity[r] += vm.res[r]
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

def auto_vmreqs_beta_variation(start, end, round_to_hour=True,
                               servers=[], **kwargs):
    """Generate VMRequests s.t. the requested resources do not exceed
    (on the average) max_cloud_usage of the available cloud capacity
    and that their beta values are varied based on the beta_option.

    """
    events = auto_vmreqs(start, end, round_to_hour, servers, **kwargs)
    beta_values = generate_beta(beta_option, len(events))
    for i, e in enumerate(events):
        e.vm.beta = beta_values[i]
    return events

def generate_beta(option, vm_number):
    """
    generate beta values of the vms based on synthetic data
    """
    if option == 1: # beta is generated based on synthetic data read from a file
        all__values = workload_beta_data()
        values_of_beta = synthetic_beta_population(vm_number, all__values)
    if option == 2: # beta is read directly from a file
        all__values = workload_beta()
        values_of_beta = all__values['beta'].values[:vm_number]
    if option == 3: # beta=fixed_beta_value for all VMs
        values_of_beta = np.ones(vm_number) * fixed_beta_value

    return values_of_beta

def normal_vmreqs(start, end, round_to_hour=True, **kwargs):
    """Generate the VM creation and deletion events in.
    Normally distributed arrays - VM sizes and durations.
    @param start, end - time interval (events within it)

    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    delta = end - start
    # array of VM sizes
    cpu_sizes = distribution_population(VM_num, min_cpu, max_cpu,
                                        distribution=resource_distribution)
    ram_sizes = distribution_population(VM_num, min_ram, max_ram,
                                        distribution=resource_distribution)
    # duration of VMs
    durations = distribution_population(VM_num, min_duration, max_duration,
                                        distribution=resource_distribution)
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

def uniform_vmreqs_beta_variation(start, end, round_to_hour=True, **kwargs):
    """Generate the VM creation and deletion events for
    uniform VM sizes. Read the CPU-boundedness of each VM
    from the file specified by USAGE_LOC.

    @param start, end - time interval (events within it)

    """

    start, end = pd.Timestamp(start), pd.Timestamp(end)
    delta = end - start
    # array of VM sizes
    cpu_sizes = distribution_population(VM_num, min_cpu, max_cpu,
                                        distribution=resource_distribution)
    ram_sizes = distribution_population(VM_num, min_ram, max_ram,
                                        distribution=resource_distribution)
    # duration of VMs
    durations = distribution_population(VM_num, min_duration, max_duration,
                                        distribution=resource_distribution)
    # TODO: add price for each VM

    beta_values = generate_beta(beta_option,VM_num)

    requests = []
    moments = []
    for cpu_size, ram_size, duration, beta_value in zip(cpu_sizes, ram_sizes,
                                                        durations, beta_values):
        vm = VM(ram_size, cpu_size)
        vm.beta = beta_value # CPU-boundedness or performance indicator (beta)
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

## OLD APPROACH
## - hardcoded values in different functions
########

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

def get_workload_loc(filename):
    return os.path.join(conf.USAGE_LOC, filename)

def get_data_loc(filename):
    return os.path.join(conf.DATA_LOC, filename)

# these methods not really necessary any more (apart for quick testing)
# separate conf files can be created to mimic them

def get_data_loc_usa(filename):
    return os.path.join(conf.DATA_LOC_USA, filename)

def get_data_loc_world(filename):
    return os.path.join(conf.DATA_LOC_WORLD, filename)

def usa_el(start=None, filepath=None):
    if filepath is None:
        filepath = get_data_loc_usa('prices.csv')
    el_prices = pd.read_csv(filepath,
                            index_col=0, parse_dates=[0])
    return el_prices

def workload_beta(start=None, filepath=None):
    if filepath is None:
        filepath = get_workload_loc('beta_test.csv')
    beta = pd.read_csv(filepath, index_col=0)# parse_dates=[0])
    #print beta
    return beta

def workload_beta_data(start=None, filepath=None):
    if filepath is None:
        filepath = get_workload_loc('beta_data_test.csv')
    beta_data = pd.read_csv(filepath)# , index_col=0
    #print beta
    return beta_data['mean']

def usa_temperature(start=None, filepath=None):
    if filepath is None:
        filepath = get_data_loc_usa('temperatures.csv')
    temperature = pd.read_csv(filepath, index_col=0, parse_dates=[0])
    return temperature

def world_el(start=None, filepath=None):
    if filepath is None:
        filepath = get_data_loc_world('prices.csv')
    el_prices = pd.read_csv(filepath, index_col=0, parse_dates=[0])
    return el_prices

def world_temperature(start=None, filepath=None):
    if filepath is None:
        filepath = get_data_loc_world('temperatures.csv')
    temperature = pd.read_csv(filepath, index_col=0, parse_dates=[0])
    return temperature

def usa_small_infrastructure():
    return small_infrastructure(['MI-Detroit', 'IN-Indianapolis'])

def usa_two_days():
    return two_days('2010-01-02 00:00')

def world_two_days():
    return two_days('2010-01-03 00:00')

def usa_two_hours():
    return two_hours('2010-01-02 00:00')

def world_two_hours():
    return two_hours('2010-01-03 00:00')

def usa_three_months():
    return pd.date_range('2010-01-02 00:00', '2010-03-30 23:00', freq='H')

def world_three_months():
    return pd.date_range('2010-01-03 00:00', '2010-03-30 23:00', freq='H')

def usa_whole_period():
    #return pd.date_range('2010-01-02 00:00', '2010-12-30 23:00', freq='H')
    el_prices = usa_el()
    start, end = el_prices.index[0], el_prices.index[-26]
    return pd.date_range(start, end, freq='H')

# dynamic visualisation
#----------------------
dynamic_cities = ['MI-Detroit', 'IN-Indianapolis']
def dynamic_usa_times():
    #start = pd.Timestamp('2010-04-25 00:00')
    start = pd.Timestamp('2010-10-12 00:00')
    end = start + pd.offsets.Day(1)
    #end = start + pd.offsets.Hour(2)
    return pd.date_range(start, end, freq='H')

def dynamic_usa_el():
    times = dynamic_usa_times()
    start, end = times[0], times[-1]
    return usa_el()[dynamic_cities][start:end]

def dynamic_usa_temp():
    times = dynamic_usa_times()
    start, end = times[0], times[-1]
    return usa_temperature()[dynamic_cities][start:end]

def dynamic_infrastructure():
    return small_infrastructure(dynamic_cities)
#----------------------
########


# geotemporal inputs
#--------------------
def parse_dataset(filepath):
    """Parse a file with CSV values (e.g. temperatures or el. prices)
    into a pandas.DataFrame.

    """
    df = pd.read_csv(filepath,
                     index_col=0, parse_dates=[0])
    return df

def times_from_conf():
    return conf.times

def el_prices_from_conf():
    el_prices = parse_dataset(conf.el_price_dataset)
    return el_prices

def temperature_from_conf():
    temperature = parse_dataset(conf.temperature_dataset)
    return temperature

def _override_settings():
    """override module settings with the config file"""
    for key, value in conf.inputgen_settings.iteritems():
        globals()[key] = value

def modify_existing_input():
    """Entry function to modify the already existing input."""
    _override_settings()
    requests = pd.read_pickle(common_loc('workload/requests.pkl'))
    beta_values = generate_beta(beta_option, len(requests))
    for req, beta in zip(requests, beta_values):
        req.vm.beta = beta
    requests.to_pickle(common_loc('workload/requests.pkl'))
    info('Modified requests and wrote them to {}'.format(
        common_loc('workload/requests.pkl'))
    )
    info(requests)

# initial input generation
#--------------------------

location_dataset = usa_el

def generate_fixed_input():
    """Entry function to generate servers and requests based
    on the desired simulation time period and locations.

    """
    _override_settings()
    df = parse_dataset(location_dataset)
    locations = df.columns.values
    start, end = conf.start, conf.end
    info('Generating input datasets\n-------------------------\nParameters:\n' +
         '- location_dataset: {}\n'.format(location_dataset) +
         '- times: {} - {}\n'.format(start, end)
    )
    info('Locations:\n{}\n'.format(locations))
    cloud = normal_infrastructure(locations) #TODO: method as parameter
    generate_requests = globals()[VM_request_generation_method]
    requests = generate_requests(start, end, servers=cloud.servers)
    with open(common_loc('workload/servers.pkl'), 'w') as pkl_srv:
        pickle.dump(cloud, pkl_srv)
    requests.to_pickle(common_loc('workload/requests.pkl'))
    info('Servers:\n{}\n'.format(cloud.servers))
    info('Requests:\n{}\n'.format(requests))
    info('Wrote to {}:\n - servers.pkl\n - requests.pkl\n'.format(
        common_loc('workload')))

def servers_from_pickle():
    with open(common_loc('workload/servers.pkl')) as pkl_srv:
        return pickle.load(pkl_srv)

# TODO: add offset
def requests_from_pickle(*args, **kwargs): # TODO: don't need input
    requests = pd.read_pickle(common_loc('workload/requests.pkl'))
    if 'offset' in kwargs:
        offset = kwargs['offset']
        requests.index = requests.index + offset
    return requests

if __name__ == '__main__':
    generate_fixed_input()
