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

import pickle
from datetime import datetime
import pprint

from philharmonic import conf
if conf.plotserver:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
else:
    import matplotlib.pyplot as plt
import pandas as pd

import philharmonic as ph
from philharmonic.logger import *
import inputgen
from .results import serialise_results
from philharmonic import Schedule
from philharmonic.scheduler.generic.fbf_optimiser import FBFOptimiser
from philharmonic.manager.imanager import IManager
#from philharmonic.cloud.driver import simdriver
from philharmonic.scheduler import NoScheduler
from philharmonic.scheduler.peak_pauser.peak_pauser import PeakPauser
from environment import SimulatedEnvironment, PPSimulatedEnvironment
from philharmonic.utils import loc, common_loc, input_loc


# old scheduler design...
#-------------------------

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


#TODO:
# - shorthand to access temp, price in server

# new simulator design
#----------------------



class Simulator(IManager):
    """simulates the passage of time and prepares all the data for
    the scheduler

    """

    factory = {
        "scheduler": "PeakPauser",
        "environment": "GASimpleSimulatedEnvironment",
        "cloud": "peak_pauser_infrastructure",
        "driver": "simdriver",

        "times": "two_days",
        "requests": None, #inputgen.normal_vmreqs,
        "servers": None, #inputgen.small_infrastructure,

        "el_prices": "simple_el",
        "temperature": "simple_temperature",
    }

    def __init__(self, factory=None, custom_scheduler=None):
        if factory is not None:
            self.factory = factory
        if custom_scheduler is not None:
            self.custom_scheduler = custom_scheduler
        super(Simulator, self).__init__()
        self.environment.el_prices = self._create(inputgen,
                                                  self.factory['el_prices'])
        self.environment.temperature = self._create(inputgen,
                                                    self.factory['temperature'])
        SD_el = self.factory['SD_el'] if 'SD_el' in self.factory  else 0
        SD_temp = self.factory['SD_temp'] if 'SD_temp' in self.factory  else 0
        self.environment.model_forecast_errors(SD_el, SD_temp)
        self.real_schedule = Schedule()

    def apply_actions(self, actions):
        """apply actions (or requests) on the cloud (for "real") and log them"""
        self.cloud.reset_to_real()
        for t, action in actions.iteritems():
            #debug('apply %s at time %d'.format(action, t))
            self.cloud.apply_real(action)
            self.real_schedule.add(action, t)
            self.driver.apply_action(action, t)

    def prompt(self):
        if conf.prompt_show_cloud:
            if conf.prompt_ipdb:
                import ipdb; ipdb.set_trace()
            else:
                prompt_res = raw_input('Press enter to continue...')

    def show_cloud_usage(self):
        self.cloud.show_usage()
        self.prompt()

    def run(self, steps=None):
        """Run the simulation. Iterate through the times, query for
        geotemporal inputs, reevaluate the schedule and simulate actions.

        @param steps: number of time steps to make through the input data
        (if None, go through the whole input)

        """

        if conf.show_cloud_interval is not None:
            t_show = conf.start + conf.show_cloud_interval
        self.scheduler.initialize()
        passed_steps = 0
        for t in self.environment.itertimes(): # iterate through all the times
            passed_steps += 1
            if steps is not None and passed_steps > steps:
                break
            # get requests & update model
            # these are the event triggers
            # - we find any requests that might arise in this interval
            requests = self.environment.get_requests()
            # - apply requests on the simulated cloud
            self.apply_actions(requests)
            if len(requests) > 0:
                #import ipdb; ipdb.set_trace()
                pass
            # call scheduler to decide on actions
            schedule = self.scheduler.reevaluate()
            self.cloud.reset_to_real()
            period = self.environment.get_period()
            actions = schedule.filter_current_actions(t, period)
            if len(requests) > 0:
                debug('Requests:\n{}\n'.format(requests))
            if len(actions) > 0:
                debug('Applying:\n{}\n'.format(actions))
            planned_actions = schedule.filter_current_actions(t + period)
            if len(planned_actions) > 0:
                debug('Planned:\n{}\n'.format(planned_actions))
            self.apply_actions(actions)
            if conf.show_cloud_interval is not None and t == t_show:
                t_show = t_show + conf.show_cloud_interval
                self.show_cloud_usage()
        return self.cloud, self.environment, self.real_schedule

# TODO: these other simulator subclasses should not be necessary
class PeakPauserSimulator(Simulator):
    def __init__(self, factory=None):
        if factory is not None:
            self.factory = factory
        self.factory["scheduler"] = "PeakPauser"
        self.factory["environment"] = "PPSimulatedEnvironment"
        super(PeakPauserSimulator, self).__init__()

    def run(self): #TODO: use Simulator.run instead
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
            # call scheduler to create new cloud state (if an action is made)
            schedule = self.scheduler.reevaluate()
            # TODO: when an action is applied to the current state, forward it
            # to the driver as well
            period = self.environment.get_period()
            actions = schedule.filter_current_actions(timestamp, period)
            self.apply_actions(actions)
        # TODO: use schedule instance
        #events = self.cloud.driver.events

from philharmonic.scheduler import FBFScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
class FBFSimulator(Simulator):
    def __init__(self, factory=None):
        if factory is not None:
            self.factory = factory
        self.factory["scheduler"] = "FBFScheduler"
        self.factory["environment"] = "FBFSimpleSimulatedEnvironment"
        super(FBFSimulator, self).__init__()

class NoSchedulerSimulator(Simulator):
    def __init__(self):
        self.factory["scheduler"] = "NoScheduler"
        super(NoSchedulerSimulator, self).__init__()


#-- common functions --------------------------------

def log_config_info(simulator):
    """Log the essential configuration information."""
    info('- output_folder: {}'.format(conf.output_folder))
    if conf.factory["times"] == "times_from_conf":
        info('- times: {} - {}'.format(conf.start, conf.end))
    if conf.factory["el_prices"] == "el_prices_from_conf":
        info('- el_price_dataset: {}'.format(conf.el_price_dataset))
    if conf.factory["temperature"] == "temperature_from_conf":
        info('- temperature_dataset: {}'.format(conf.temperature_dataset))
    info('- forecasting:')
    info('  * periods: {}'.format(conf.factory['forecast_periods']))
    info('  * errors: SD_el={}, SD_temp={}'.format(
        conf.factory['SD_el'], conf.factory['SD_temp']
    ))
    info('\n- scheduler: {}'.format(conf.factory['scheduler']))
    if conf.factory['scheduler_conf'] is not None:
        info('  * conf: \n{}'.format(
            pprint.pformat(conf.factory['scheduler_conf'])
        ))

    info('\nServers ({} -> will copy to: {})\n-------\n{}'.format(
        common_loc('workload/servers.pkl'),
        os.path.relpath(input_loc('servers.pkl')),
        simulator.cloud.servers
        #pprint.pformat(simulator.cloud.servers)
        #simulator.cloud.show_usage()
    ))
    if conf.power_freq_model is not False:
        info('\n- freq. scale from {} to {} by {}.'.format(
            conf.freq_scale_min, conf.freq_scale_max, conf.freq_scale_delta
        ))
    info('\nRequests ({} -> will copy to: {})\n--------\n{}\n'.format(
        common_loc('workload/requests.pkl'),
        os.path.relpath(input_loc('requests.pkl')),
        simulator.requests)
    )
    if conf.prompt_configuration:
        prompt_res = raw_input('Config good? Press enter to continue...')

def archive_inputs(simulator):
    """copy input files together with the results (for archive reasons)"""
    with open(input_loc('servers.pkl'), 'w') as pkl_srv:
        pickle.dump(simulator.cloud, pkl_srv)
    simulator.requests.to_pickle(input_loc('requests.pkl'))

def before_start(simulator):
    log_config_info(simulator)
    archive_inputs(simulator)

#-- simulation starter ------------------------------

# schedule.py routes straight to here

# TODO: make run a method of Simulator maybe?

def run(steps=None, custom_scheduler=None):
    """Run the simulation."""
    info('\nSETTINGS\n########\n')

    # create simulator from the conf
    #-------------------------------
    simulator = Simulator(conf.get_factory(), custom_scheduler)

    before_start(simulator)

    # run the simulation
    #-------------------
    info('\nSIMULATION\n##########\n')
    start_time = datetime.now()
    info('Simulation started at time: {}'.format(start_time))
    cloud, env, schedule = simulator.run(steps)
    info('RESULTS\n#######\n')

    # serialise and log the results
    #------------------------------
    results = serialise_results(cloud, env, schedule)

    end_time = datetime.now()
    info('Simulation finished at time: {}'.format(end_time))
    info('Duration: {}\n'.format(end_time - start_time))
    return results

if __name__ == "__main__":
    run()

#-----------------------------------------------------
