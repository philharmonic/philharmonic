'''
Created on Oct 9, 2012

@author: kermit
'''

import os
import pandas as pd

# I/O
#======

# experimental workflow
#----------------------
historical_en_prices = "./io/energy_price/train/3month.csv"
#historical_en_prices = "./io/energy_price_data-quick_test.csv"
#historical_en_prices = "./io/energy_price_data-single_day.csv"

save_power = False
#----------------------

# stop and check settings with user (only initially)
prompt_configuration = True
# interval at which to print cloud usage: pd.offsets.* or None
show_cloud_interval = pd.offsets.Hour(1)
# stop the simulation for inspection?
prompt_show_cloud = False
prompt_ipdb = True

common_output_folder = "io/"
base_output_folder = os.path.join(common_output_folder, "results/test/")
output_folder = base_output_folder

DATA_LOC = os.path.expanduser('~/Dropbox/dev/skripte/python/notebook')
DATA_LOC = os.path.join(DATA_LOC, 'tu/data/geotemporal')

# the datasets used in the simulation
USA = False
if USA:
    temperature_dataset = os.path.join(DATA_LOC, 'temperatures.csv')
    el_price_dataset = os.path.join(DATA_LOC, 'prices.csv')
else:
    temperature_dataset = os.path.join(DATA_LOC, 'world-realtemp/temperatures.csv')
    el_price_dataset = os.path.join(DATA_LOC, 'world-realtemp/prices.csv')

# the time period of the simulation
start = pd.Timestamp('2010-06-03 00:00')
# - two days
#times = pd.date_range(start, periods=24 * 7, freq='H')
times = pd.date_range(start, periods=2, freq='H')
end = times[-1]

# plotting results
plotserver = True
#plotserver = False
if plotserver: # plotting in GUI-less environment
    liveplot = False
else: # GUI present (desktop OS)
    liveplot = False
    #liveplot = True
    fileplot = False


# Manager
#=========
# Manager - actually sleeps and wakes up the scheduler
# Simulator - just runs through the simulation
manager = "Simulator"

# Manager factory
#=================

factory = {
    # Scheduling algorithm to use. Can be:
    #  FBFScheduler, BFDScheduler, GAScheduler, NoScheduler
    "scheduler": "FBFScheduler",
    # Optional object to pass to the scheduler for parameters
    "scheduler_conf": None,
    # The environment class (for iterating through simulation timestamps)
    "environment": "GASimpleSimulatedEnvironment",
    # Available cloud infrastructure. Can be:
    #  servers_from_pickle (recommended), small_infrastructure,
    #  usa_small_infrastructure, dynamic_infrastructure
    "cloud": "servers_from_pickle",

    "forecast_periods": 12,
    ### no error
    "SD_el": 0,
    "SD_temp": 0,
    ### small error
    #"SD_el": 0.01,
    #"SD_temp": 1.41,
    ### medium error
    #"SD_el": 0.03,
    #"SD_temp": 3,
    ### large error
    #"SD_el": 0.05,
    #"SD_temp": 5,

    # Timestamps of the simulation. Can be:
    #  times_from_conf (take times from conf.times, recommended),
    #  two_days, world_three_months,
    #  usa_two_hours, usa_two_days, usa_three_months
    #  world_two_hours, world_two_days, world_three_months
    #  dynamic_usa_times, usa_whole_period
    "times": "times_from_conf",

    # VM requests. Can be:
    #  requests_from_pickle (recommended), simple_vmreqs, medium_vmreqs
    "requests": "requests_from_pickle",
    # offset by which to shift requests (None for no shifting)
    # - mostly just for use by the explorer
    "requests_offset": None,
    # Geotemporal inputs. *_from_conf recommended
    # (they read CSV files located at conf.*_dataset)
    # Can also be:
    #  simple_el, medium_el, usa_el, world_el, dynamic_usa_el
    #  simple_temperature, medium_temperature, usa_temperature,
    #  world_temperature, dynamic_usa_temp
    "el_prices": "el_prices_from_conf",
    "temperature": "temperature_from_conf",

    # Driver that takes the manager's actions and controls the cloud:
    #  nodriver (no actions)
    #  simdriver (only logs actions)
    #  (real OpenStack driver not implemented yet)
    "driver": "nodriver",
}

def get_factory():
    return factory

# Various scheduling settings
#============================
# Percentage of utilisation under which a PM is considered underutilised
underutilised_threshold = 0.5

# inputgen settings
#==================

inputgen_settings = {
    # cloud's servers
    'location_dataset': temperature_dataset,
    #'server_num': 3,
    'server_num': 20,
    #'server_num': 50,
    #'server_num': 200,
    #'server_num': 2000,
    'min_server_cpu': 8,
    'max_server_cpu': 16,
    'min_server_ram': 16,
    'max_server_ram': 32,

    # VM requests
    # TODO: auto / manual
    # method of generating requests: normal_vmreqs, auto_vmreqs
    'VM_request_generation_method': 'auto_vmreqs',
    #'VM_num': 80,
    'VM_num': 5, # only important with normal_vmreqs, not auto_vmreqs
    #'VM_num': 2000,
    # e.g. CPUs
    'min_cpu': 1,
    'max_cpu': 2,
    'min_ram': 2,
    'max_ram': 4,
    # e.g. seconds
    'min_duration': 60 * 60, # 1 hour
    #'max_duration': 60 * 60 * 3, # 3 hours
    'max_duration': 60 * 60 * 24 * 3, # 2 days
    #'max_duration': 60 * 60 * 24 * 10, # 10 days
    #'max_duration': 60 * 60 * 24 * 90, # 90 days
}

# Benchmark
#===========

# if dummy == True, will do just a local dummy benchmark,
# faking all the OpenStack commands
dummy = True
#dummy = False
# for False set all these other settings...

# host on which the benchmark VM is deployed (for energy measurements)
host = "snowwhite"

# VM (instance) which executes the benchmark
instance = "kermit-test"

# The command to execute as a benchmark (use ssh to execute something in a VM).
# If command=="noscript" then just some local execution will be done
#command="noscript"
#command = "/usr/bin/ssh 192.168.100.4 ls"
#command = "./io/benchmark.sh"
command = "./io/benchmark-local.sh"


# how many % of hours in a day should the VM be paused
#percentage_to_pause = 0.04 # *100%
percentage_to_pause = 0.15 # *100%

# time to sleep between checking if the benchmark finished or needs to be paused
sleep_interval = 1 # seconds
