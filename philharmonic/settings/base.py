'''
Created on Oct 9, 2012

@author: kermit
'''

import os
import pandas as pd
# import numpy as np
# import pylab as pl

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
prompt_configuration = False
# interval at which to print cloud usage: pd.offsets.* or None
show_cloud_interval = pd.offsets.Hour(1)
# stop the simulation for inspection?
prompt_show_cloud = False
prompt_ipdb = True

common_output_folder = "io/"
base_output_folder = os.path.join(common_output_folder, "results/test/")
output_folder = base_output_folder


USAGE_LOC = "io/usage/" # path from the philharmonic root
# from this module to philharmonic root and then to USAGE_LOC
USAGE_LOC = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                         '../..', USAGE_LOC))
DATA_LOC = "io/geotemp/" # path from the philharmonic root
# from this module to philharmonic root and then to DATA_LOC
DATA_LOC = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                         '../..', DATA_LOC))

# the datasets used in the simulation
USA = False # USA or world-wide
FIXED_EL_PRICES = False # fixed el. prices world-wide
DATA_LOC_USA = os.path.join(DATA_LOC, "usa/")
DATA_LOC_WORLD = os.path.join(DATA_LOC, "world/")
DATA_LOC_WORLD_FIXED_EL = os.path.join(DATA_LOC, "world-fixed_el/")
if USA:
    DATA_LOC = DATA_LOC_USA
else:
    DATA_LOC = DATA_LOC_WORLD
    if FIXED_EL_PRICES:
        DATA_LOC = DATA_LOC_WORLD_FIXED_EL
temperature_dataset = os.path.join(DATA_LOC, 'temperatures.csv')
el_price_dataset = os.path.join(DATA_LOC, 'prices.csv')

# the time period of the simulation
start = pd.Timestamp('2010-06-03 00:00')

# - five hours
#times = pd.date_range(start, periods=6, freq='H')
# - one day
#times = pd.date_range(start, periods=24, freq='H')
# - one week
times = pd.date_range(start, periods=24 * 7, freq='H')
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
    # general settings
    #  - the statistical distribution to draw resources and duration from
    #    ( uniform or normal)
    'resource_distribution': 'uniform',

    # cloud's servers
    'location_dataset': temperature_dataset,
    #'server_num': 3,
    #'server_num': 1,
    #'server_num': 50,
    #'server_num': 100,
    #'server_num': 200,
    'server_num': 1200,
    #'server_num': 2000,
    #'min_server_cpu': 8,
    'min_server_cpu': 1, # 16,
    'max_server_cpu': 4, # 16,
    #'max_server_cpu': 4, # 16,
    'min_server_ram': 16, # 32,
    'max_server_ram': 32, # 32,
    # 1 to generate beta, 2 to read them directly from file and
    # 3 for all beta equal to 1
    'beta_option': 3,
    'fixed_beta_value': 1.,
    'max_cloud_usage': 0.8,

    # VM requests
    # method of generating requests: normal_vmreqs, auto_vmreqs
    'VM_request_generation_method': 'auto_vmreqs',
    'VM_num': 2000,
    #'VM_num': 5, # only important with normal_vmreqs, not auto_vmreqs
    #'VM_num': 2000,
    # e.g. CPUs
    'min_cpu': 1, # 8,
    'max_cpu': 1, # 8,
    'min_ram': 8, # 2,
    'max_ram': 32, # 28,
    # e.g. seconds
    'min_duration': 60 * 60, # 1 hour
    #'max_duration': 60 * 60 * 3, # 3 hours
    #'max_duration': 60 * 60 * 6, # 6 hours
    #'max_duration': 60 * 60 * 24, # 24 hours
    #'max_duration': 60 * 60 * 24 * 3, # 2 days
    'max_duration': 60 * 60 * 24 * 7, # one week
    #'max_duration': 60 * 60 * 24 * 10, # 10 days
    #'max_duration': 60 * 60 * 24 * 90, # 90 days
}

# Simulation details
#===================

# the frequency at which to generate the power signals
power_freq = '5min'
# various power values of the servers in Watts
P_peak = 200
P_idle = 100
# the standard deviation of the power signal
# P_std = 5
P_std = 0
P_base = 150
P_dif = 15
# VM cost components
C_base = 0.027028 #0.0520278  # in future use C_base = 0.027028
C_dif_cpu = 0.018
C_dif_ram = 0.025
# CPU frequency parameters
f_max = 2600 # the maximum CPU frequency in MHz
power_freq_model = True # consider CPU frequency in the power model
# TODO: apply to model
freq_scale_max = 1.0
freq_scale_digits = 5
freq_scale_min = round(1800./2600, 1) # = 0.7
freq_scale_delta = round((freq_scale_max - freq_scale_min) / 4,
                         freq_scale_digits) # = 0.075
f_min = f_max * freq_scale_min
f_base = 1000

# freq_scales = np.round(frange(freq_scale_max, freq_scale_min,
#                                  delta=-freq_scale_delta),
#                        freq_scale_digits)

# pricing
# the frequency at which to generate the VM price is calculated
pricing_freq = '1h'

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
