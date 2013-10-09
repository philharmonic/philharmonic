import pandas as pd

import inputgen
from philharmonic.logger import *

"""The philharmonic simulator.

Traces geotemporal input data, asks the scheduler to determine actions
and simulates the outcome of the schedule.
"""

# inputs
# -------
def infrastructure_info():
    info(" - generating aritficial infrastructure")
    return inputgen.small_infrastructure()

def geotemporal_inputs():
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
    """change servers by setting a location"""
    #Todo: Potentially separate into DCs
    for i, s in enumerate(servers):
        s.loc = possible_locations[i]

# main run
# --------
def run(steps=None):
    """run the simulation
    @param steps: number of time steps to make through the input data
    (None - go through the whole input)
    """
    info("simulation started")
    servers = infrastructure_info()
    el_prices, temperatures = geotemporal_inputs()
    server_locations(servers, temperatures.columns)

    # first version - iterate through all the hours
    times = temperatures[temperatures.columns[0]].index
    if steps==None:
        steps = 10
    for t in times[:steps]:
        info(" - now at step {0}".format(t))
        for s in servers:
            info('   * server {0} - el.: {1}, temp.: {2}'
                 .format(s, el_prices[s.loc][t], temperatures[s.loc][t]))

#TODO:
# - shorthand to access temp, price in server
# - print info in detailed function



if __name__ == "__main__":
    run()
