import pandas as pd

from philharmonic.logger import *
import inputgen

"""The philharmonic simulator.

Traces geotemporal input data, asks the scheduler to determine actions
and simulates the outcome of the schedule.

"""


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



    for t in times[:steps-1]: # iterate through all the hours
        # print info
        debug(" - now at step {0}".format(t))
        for s in servers:
            debug('   * server {0} - el.: {1}, temp.: {2}'
                 .format(s, el_prices[s.loc][t], temperatures[s.loc][t]))
        # these are the event triggers
        # - group requests for that step
        new_requests = requests[t:t+freq]
        debug(' - new requests:')
        debug(str(new_requests))
        # - we get new data about the future temp. and el. prices
        known_data = prepare_known_data((el_prices, temperatures), t)
        debug(known_data[0].index)
        # call scheduler to decide on actions

    # perform the actions somehow


#TODO:
# - shorthand to access temp, price in server
# - print info in detailed function

if __name__ == "__main__":
    run()
