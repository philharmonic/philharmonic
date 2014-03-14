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

    factory = {
        "scheduler": GAScheduler,
        "environment": GASimpleSimulatedEnvironment,
        #"cloud": inputgen.small_infrastructure,
        "cloud": inputgen.usa_small_infrastructure,
        "driver": simdriver,

        #"times": inputgen.two_days,
        "times": inputgen.usa_two_days,
        "requests": inputgen.simple_vmreqs,
        "servers": inputgen.small_infrastructure,

        #"el_prices": inputgen.simple_el,
        "el_prices": inputgen.usa_el,
        #"temperature": inputgen.simple_temperature,
        "temperature": inputgen.usa_temperature,
    }

    return factory

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
