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

# stop and check settings with user
prompt_configuration = True

common_output_folder = "io/"
output_folder = "io/results/"

DATA_LOC = os.path.expanduser('~/Dropbox/dev/skripte/python/notebook')
DATA_LOC = os.path.join(DATA_LOC, 'tu/data/geotemporal')

# the datasets used in the simulation
temperature_dataset = os.path.join(DATA_LOC, 'world-realtemp/temperatures.csv')
el_price_dataset = os.path.join(DATA_LOC, 'world-realtemp/temperatures.csv')

# the time period of the simulation
start = pd.Timestamp('2010-01-03 00:00')
# - two days
times = pd.date_range(start, periods=48, freq='H')
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

# use strings and import lazily using importlib. Don't import directly.
from philharmonic.scheduler import FBFScheduler, GAScheduler, BFDScheduler

# environments
from philharmonic.simulator.environment import GASimpleSimulatedEnvironment

from philharmonic.simulator import inputgen
from philharmonic.cloud.driver import simdriver

factory = {
    "scheduler": FBFScheduler,
    "scheduler_conf": None,
    "environment": GASimpleSimulatedEnvironment,
    #"cloud": inputgen.small_infrastructure,
    #"cloud": inputgen.usa_small_infrastructure,
    "cloud": inputgen.servers_from_pickle,
    #"cloud": inputgen.dynamic_infrastructure,

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

    #"times": inputgen.two_days,
    #"times": inputgen.usa_two_hours,
    #"times": inputgen.usa_two_days,
    #"times": inputgen.usa_three_months,
    #"times": inputgen.world_two_hours,
    "times": inputgen.world_two_days,
    #"times": inputgen.world_three_months,
    #"times": inputgen.dynamic_usa_times,
    #"times": inputgen.usa_whole_period,
    #"requests": inputgen.simple_vmreqs,
    #"requests": inputgen.medium_vmreqs,
    "requests": inputgen.requests_from_pickle,

    #"el_prices": inputgen.simple_el,
    #"el_prices": inputgen.medium_el,
    #"el_prices": inputgen.usa_el,
    "el_prices": inputgen.world_el,
    #"el_prices": os.path.join(DATA_LOC, 'world-realtemp/prices.csv'),
    #"el_prices": inputgen.dynamic_usa_el,
    #"temperature": inputgen.simple_temperature,
    #"temperature": inputgen.medium_temperature,
    #"temperature": inputgen.usa_temperature,
    "temperature": inputgen.world_temperature,
    #"temperature": inputgen.dynamic_usa_temp,

    "driver": simdriver,
}

def get_factory():
    #return get_factory_ga()
    return factory

# inputgen settings
#==================

inputgen_settings = {
    # cloud's servers
    'location_dataset': temperature_dataset,
    'server_num': 20,
    'min_server_cpu': 4,
    'max_server_cpu': 8,
    'min_server_ram': 4,
    'max_server_ram': 8,

    # VM requests
    #'VM_num': 80,

    'VM_num': 5,
    #'VM_num': 2000,
    # e.g. CPUs
    'min_cpu': 1,
    'max_cpu': 2,
    'min_ram': 1,
    'max_ram': 2,
    # e.g. seconds
    'min_duration': 60 * 60, # 1 hour
    #'max_duration': 60 * 60 * 3, # 3 hours
    'max_duration': 60 * 60 * 24 * 2, # 2 days
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
