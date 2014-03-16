'''
Created on Oct 9, 2012

@author: kermit
'''

# I/O
#======

historical_en_prices = "./io/energy_price/train/3month.csv"
#historical_en_prices = "./io/energy_price_data-quick_test.csv"
#historical_en_prices = "./io/energy_price_data-single_day.csv"

results = "./io/results.pickle"

# Manager
#=========
# Manager - actually sleeps and wakes up the scheduler
# Simulator - just runs through the simulation
manager = "Simulator"

# Manager factory
#=================

# won't have to be function once I kick out conf from PeakPauser
def get_factory_fbf():
    # these schedulers are available:
    from philharmonic.scheduler import PeakPauser, NoScheduler, FBFScheduler

    # environments
    from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

    from philharmonic.simulator import inputgen
    from philharmonic.cloud.driver import simdriver

    factory = {
        "scheduler": FBFScheduler,
        "environment": FBFSimpleSimulatedEnvironment,
        "cloud": inputgen.small_infrastructure,
        "driver": simdriver,

        "times": inputgen.two_days,
        "requests": inputgen.normal_vmreqs,
        "servers": inputgen.small_infrastructure,
    }

    return factory

def get_factory_ga():
    # these schedulers are available:
    from philharmonic.scheduler import GAScheduler

    # environments
    from philharmonic.simulator.environment import GASimpleSimulatedEnvironment

    from philharmonic.simulator import inputgen
    from philharmonic.cloud.driver import simdriver

    gaconf = {
        "population_size": 30,
        "recombination_rate": 0.15,
        "mutation_rate": 0.05,
        "max_generations": 20,
    }

    factory = {
        "scheduler": GAScheduler,
        "scheduler_conf": gaconf,
        "environment": GASimpleSimulatedEnvironment,
        #"cloud": inputgen.small_infrastructure,
        "cloud": inputgen.usa_small_infrastructure,
        "driver": simdriver,

        #"times": inputgen.two_days,
        #"times": inputgen.usa_two_days,
        #"times": inputgen.usa_two_hours,
        "times": inputgen.usa_whole_period,
        #"requests": inputgen.simple_vmreqs,
        "requests": inputgen.requests_from_pickle,
        #"cloud": inputgen.small_infrastructure,
        "cloud": inputgen.servers_from_pickle,

        #"el_prices": inputgen.simple_el,
        "el_prices": inputgen.usa_el,
        #"temperature": inputgen.simple_temperature,
        "temperature": inputgen.usa_temperature,
    }

    return factory

# Simulator settings
#===========================

#liveplot = True
liveplot = False

inputgen_settings = {
    # cloud's servers
    'server_num': 50,
    'min_server_cpu': 4,
    'max_server_cpu': 8,

    # VM requests
    'VM_num': 30,
    # e.g. CPUs
    'min_cpu': 1,
    'max_cpu': 2,
    'min_ram': 1,
    'max_ram': 2,
    # e.g. seconds
    'min_duration': 60 * 60, # 1 hour
    #'max_duration': 60 * 60 * 3, # 3 hours
    'max_duration': 60 * 60 * 24 * 10, # 10 days
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
