"""The philharmonic simulator.

Traces geotemporal input data, asks the scheduler to determine actions
and simulates the outcome of the schedule.

                              (_)(_)
                             /     \    ssssssimulator
                            /       |  /
                           /   \  * |
             ________     /    /\__/
     _      /        \   /    /
    / \    /  ____    \_/    /
   //\ \  /  /    \         /
   V  \ \/  /      \       /
       \___/        \_____/


"""

import pandas as pd

from philharmonic.logger import *
import inputgen
from philharmonic.scheduler.generic.fbf_optimiser import FBFOptimiser


# inputs (probably separate modules in the future, but we'll see)
# -------
def infrastructure_info():
    """Get the infrastructure definition -- number and type of servers."""

    info(" - generating aritficial infrastructure")
    return inputgen.small_infrastructure()


def geotemporal_inputs():
    """Read time series for el. prices and temperatures
    at different locations.

    """
    info(" - reading geotemporal inputs")
    freq = 'H'
    # el. prices
    el_prices_pth = 'io/geotemp/el_prices-usa.pkl'
    el_prices = pd.read_pickle(el_prices_pth)
    # - resample to desired freqency
    el_prices = el_prices.resample(freq)
    debug(str(el_prices))

    # temperatures
    temperatures_pth = 'io/geotemp/temperature-usa.pkl'
    temperatures = pd.read_pickle(temperatures_pth)
    temperatures = temperatures.resample(freq)
    debug(str(temperatures))
    # common index is actually in temperatures (subset of prices)

    return el_prices, temperatures


def server_locations(servers, possible_locations):
    """Change servers by setting a location."""
    #Todo: Potentially separate into DCs
    for i, s in enumerate(servers):
        s.loc = possible_locations[i]


def VM_requests(start, end):
    return inputgen.normal_vmreqs(start, end)


def prepare_known_data(dataset, t, future_horizon=None): # TODO: use pd.Panel for dataset
    """ @returns a subset of the @param dataset
    (a tuple of pd.TimeSeries objects)
    that is known at moment @param t

    """
    future_horizon = future_horizon or pd.offsets.Hour(4)
    el_prices, temperatures = dataset # unpack
    # known data (past and future up to a point)
    known_el_prices = el_prices[:t+future_horizon]
    known_temperatures = temperatures[:t+future_horizon]
    return known_el_prices, known_temperatures


# main run
# --------
def run(steps=None):
    """run the simulation
    @param steps: number of time steps to make through the input data
    (None - go through the whole input)
    """
    info("simulation started")

    # get the input data
    servers = infrastructure_info()
    el_prices, temperatures = geotemporal_inputs()
    server_locations(servers, temperatures.columns)

    times = temperatures[temperatures.columns[0]].index # TODO: attach this to server objects in a function
    freq = temperatures[temperatures.columns[0]].index.freq
    if steps is None:
        steps = 10 # TODO: len of shortest input

    # simulate how users will use our cloud
    requests = VM_requests(times[0], times[steps-1])
    debug(requests)

    # for t in requests.index:
    #     request = requests[t]
    #     debug(str(request))
    #     known_data = prepare_known_data((el_prices, temperatures), t)
    #     debug(known_data[0].index)
    #     # call scheduler to decide on actions

    # # perform the actions somehow

    # instantiate scheduler
    scheduler = FBFOptimiser(servers)

    for t in times[:steps-1]: # iterate through all the hours
        # print info
        debug(" - now at step {0}".format(t))
        for s in servers:
            debug('   * server {0} - el.: {1}, temp.: {2}'
                 .format(s, el_prices[s.loc][t], temperatures[s.loc][t]))
        # these are the event triggers
        # - we find any requests that might arise in this interval
        # - group requests for that step
        new_requests = requests[t:t+freq]
        debug(' - new requests:')
        debug(str(new_requests))
        # - we get new data about the future temp. and el. prices
        known_data = prepare_known_data((el_prices, temperatures), t)
        debug(known_data[0].index)
        # call scheduler to decide on actions
        scheduler.find_solution(known_data, new_requests)

    # perform the actions somehow


#TODO:
# - shorthand to access temp, price in server
# - print info in detailed function

# new simulator design
#----------------------

from philharmonic.manager.imanager import IManager
from philharmonic import conf
from philharmonic.cloud.driver import simdriver
from philharmonic.scheduler import PeakPauser, NoScheduler
from environment import SimulatedEnvironment, PPSimulatedEnvironment

class Simulator(IManager):
    """simulates the passage of time and prepares all the data for
    the scheduler

    """

    factory = {
        "scheduler": PeakPauser,
        "environment": PPSimulatedEnvironment,
        "cloud": inputgen.peak_pauser_infrastructure,
        "driver": simdriver
    }

#    def __init__(self, factory=None):
#        IManager.__init__(self, factory)

    def filter_current_actions(self, schedule, t):
        #yield action for action, t in schedule if 
        period = self.environment.get_period()
        return schedule.actions.ix[t:t + period]

    def apply_actions(self, actions):
        for t, action in actions.iteritems():
            info('apply %s at time %d'.format(action, t))
            self.driver.apply_action(action, t)

    def run(self):
        """go through all the timesteps and call the scheduler to ask for
        actions

        """
        self.environment.times = range(24)
        self.environment._period = pd.offsets.Hour(1)
        self.scheduler.initialize()
        for hour in self.environment.times:
            # TODO: set time in the environment instead of here
            timestamp = pd.Timestamp('2013-02-20 {0}:00'.format(hour))
            self.environment.set_time(timestamp)
            debug(timestamp)
            # call scheduler to create new cloud state (if an action is made)
            schedule = self.scheduler.reevaluate()
            # TODO: when an action is applied to the current state, forward it
            # to the driver as well
            actions = self.filter_current_actions(schedule, timestamp)
            #import ipdb; ipdb.set_trace()
            self.apply_actions(actions)
        events = self.cloud.driver.events
        print(events)


class PeakPauserSimulator(Simulator):
    def __init__(self):
        self.factory["scheduler"] = PeakPauser
        self.factory["environment"] = PPSimulatedEnvironment
        super(PeakPauserSimulator, self).__init__()

from philharmonic.scheduler import FBFScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
class FBFSimulator(Simulator):
    def __init__(self):
        self.factory["scheduler"] = FBFScheduler
        self.factory["environment"] = FBFSimpleSimulatedEnvironment
        super(Simulator, self).__init__()

    def run(self):
        self.scheduler.initialize()
        for t in self.environment.itertimes():
            debug(t)
            schedule = self.scheduler.reevaluate()
            actions = self.filter_current_actions(schedule, t)
            #import ipdb; ipdb.set_trace()
            self.apply_actions(actions)
        events = self.cloud.driver.events
        debug(events)

class NoSchedulerSimulator(Simulator):
    def __init__(self):
        self.factory["scheduler"] = NoScheduler
        super(NoSchedulerSimulator, self).__init__()


#-- simulation starter ------------------------------

if __name__ == "__main__":
    # run()
    from philharmonic import conf
    from philharmonic.manager import ManagerFactory
    simulator = PeakPauserSimulator()
    simulator.run()

#-----------------------------------------------------
