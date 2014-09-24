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
from philharmonic import Schedule
from philharmonic.scheduler.generic.fbf_optimiser import FBFOptimiser
from philharmonic.scheduler import evaluator
from philharmonic.manager.imanager import IManager
#from philharmonic.cloud.driver import simdriver
from philharmonic.scheduler import NoScheduler
from philharmonic.scheduler.peak_pauser.peak_pauser import PeakPauser
from environment import SimulatedEnvironment, PPSimulatedEnvironment
from philharmonic.utils import loc


# old scheduler design...
#-------------------------

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
# def run(steps=None):
#     """run the simulation
#     @param steps: number of time steps to make through the input data
#     (None - go through the whole input)
#     """
#     info("simulation started")

#     # get the input data
#     servers = infrastructure_info()
#     el_prices, temperatures = geotemporal_inputs()
#     server_locations(servers, temperatures.columns)

    times = temperatures[temperatures.columns[0]].index # TODO: attach this to server objects in a function
    freq = temperatures[temperatures.columns[0]].index.freq
    if steps is None:
        steps = 10 # TODO: len of shortest input

    requests = VM_requests(times[0], times[steps-1])
    debug(requests)

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

        scheduler.find_solution(known_data, new_requests)

    # perform the actions somehow


#TODO:
# - shorthand to access temp, price in server
# - print info in detailed function

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

    def __init__(self, factory=None):
        if factory is not None:
            self.factory = factory
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

    def run(self):
        if conf.show_cloud_interval is not None:
            t_show = conf.start + conf.show_cloud_interval
        self.scheduler.initialize()
        for t in self.environment.itertimes():
            # get requests & update model
            requests = self.environment.get_requests()
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

# TODO: these other simulator sublclasses should not be necessary
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


#-- simulation starter ------------------------------

# schedule.py routes straight to here

def pickle_results(schedule):
    schedule.actions.to_pickle(loc('schedule.pkl'))
    #with open('schedule.pkl', 'w') as pkl_schedule:
    #    pickle.dump(schedule.actions, pkl_schedule)

# TODO: make run a method on Simulator maybe?

def run():
    info('SETTINGS\n########\n')

    fig = plt.figure(1)#, figsize=(10, 15))
    fig.subplots_adjust(bottom=0.2, top=0.9, hspace=0.5)

    nplots = 4
    # create necessary objects
    #-------------------------
    simulator = Simulator(conf.get_factory())

    # log essential information
    if conf.factory["times"] == "times_from_conf":
        info('- times: {} - {}'.format(conf.start, conf.end))
    if conf.factory["el_prices"] == "el_prices_from_conf":
        info('- el_prices_dataset: {}'.format(conf.el_price_dataset))
    if conf.factory["temperature"] == "temperature_from_conf":
        info('- temperature_dataset: {}'.format(conf.temperature_dataset))
    info('- forecasting')
    info('  * periods: {}'.format(conf.factory['forecast_periods']))
    info('  * errors: SD_el={}, SD_temp={}'.format(
        conf.factory['SD_el'], conf.factory['SD_temp']
    ))
    info('\n- scheduler: {}'.format(conf.factory['scheduler']))
    if conf.factory['scheduler_conf'] is not None:
        info('  * conf: {}'.format(conf.factory['scheduler_conf']))

    info('\nServers\n-------\n{}\n'.format(simulator.cloud.servers))
    info('Requests\n--------\n{}\n'.format(simulator.requests))

    if conf.prompt_configuration:
        prompt_res = raw_input('Config good? Press enter to continue...')

    # run the simulation
    #-------------------
    info('\nSIMULATION\n##########')
    cloud, env, schedule = simulator.run()
    info('DONE\n####\n\n')
    pickle_results(schedule)
    cloud.reset_to_initial()
    info('Simulation timeline\n--------------')
    evaluator.print_history(cloud, env, schedule)
    # geotemporal inputs
    #-------------------
    ax = plt.subplot(nplots, 1, 1)
    ax.set_title('Electricity prices ($/kWh)')
    env.el_prices.plot(ax=ax)
    ax = plt.subplot(nplots, 1, 2)
    ax.set_title('Temperature (C)')
    env.temperature.plot(ax=ax)
    # cloud utilisation
    #------------------
    evaluator.precreate_synth_power(env.start, env.end, cloud.servers)
    util = evaluator.calculate_cloud_utilisation(cloud, env, schedule)
    print('Utilisation (%)')
    print(util*100)
    #print('- weighted mean per no')
    # weighted_mean(util[util>0])
    #util[util>0].mean().dropna().mean() * 100
    # TODO: maybe weighted mean for non-zero util
    # ax = plt.subplot(nplots, 1, 1)
    # ax.set_title('Utilisation (%)')
    # util.plot(ax=ax)
    # cloud power consumption
    #------------------
    power = evaluator.generate_cloud_power(util)
    if conf.save_power:
        power.to_pickle(loc('power.pkl'))
    ax = plt.subplot(nplots, 1, 3)
    ax.set_title('Computational power (W)')
    power.plot(ax=ax)
    energy = ph.joul2kwh(ph.calculate_energy(power))
    info('Energy (kWh)')
    info(energy)
    info(' - total:')
    info(energy.sum())
    # cooling overhead
    #-----------------
    #temperature = inputgen.simple_temperature()
    temperature = env.temperature
    power_total = evaluator.calculate_cloud_cooling(power, temperature)
    ax = plt.subplot(nplots, 1, 4)
    ax.set_title('Total power (W)')
    power_total.plot(ax=ax)
    if conf.save_power:
        power_total.to_pickle(loc('power_total.pkl'))
    energy_total = ph.joul2kwh(ph.calculate_energy(power_total))
    info('Energy with cooling (kWh)')
    info(energy_total)
    info(' - total:')
    info(energy_total.sum())
    # migration overhead
    #-------------------
    migration_energy, migration_cost = evaluator.calculate_migration_overhead(
        cloud, env, schedule
    )
    info('Migration energy (kWh)')
    info(migration_energy)
    info('Migration cost ($)')
    info(migration_cost)
    info(' - total with migrations:')
    info(energy_total.sum() + migration_energy)
    # electricity costs
    #------------------
    #el_prices = inputgen.simple_el()
    el_prices = env.el_prices
    cost = evaluator.calculate_cloud_cost(power, el_prices)
    info('Electricity prices ($)')
    info(cost)
    info(' - total:')
    info(cost.sum())
    cost_total = evaluator.calculate_cloud_cost(power_total, el_prices)
    info('Electricity prices with cooling ($)')
    info(cost_total)
    info(' - total:')
    info(cost_total.sum())
    info(' - total with migrations:')
    info(cost_total.sum() + migration_cost)
    # QoS aspects
    #------------------
    # Capacity constraints
    #---------------------
    # TODO: these two

    # aggregated results
    aggregated = [energy.sum(), cost.sum(),
                  energy_total.sum() + migration_energy,
                  cost_total.sum() + migration_cost]
    aggr_names = ['IT energy (kWh)', 'IT cost ($)',
                  'Total energy (kWh)', 'Total cost ($)']
    aggregated_results = pd.Series(aggregated, aggr_names)
    aggregated_results.to_pickle(loc('results.pkl'))
    #aggregated_results.plot(kind='bar')
    info(aggregated_results)

    if conf.liveplot:
        plt.show()
    elif conf.liveplot:
        plt.savefig(loc('results-graph.pdf'))

    info('Done. Results saved to: {}'.format(conf.output_folder))

if __name__ == "__main__":
    run()

#-----------------------------------------------------
