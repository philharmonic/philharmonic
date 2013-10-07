import inputgen
from philharmonic.logger import *

"""The philharmonic simulator.

Traces geotemporal input data, asks the scheduler to determine actions
and simulates the outcome of the schedule.
"""

def run(steps=None):
    """run the simulation
    @param steps: number of time steps to make through the input data
    (None - go through the whole input)
    """
    info("simulation started")
    info(" - generating aritficial infrastructure")
    servers = inputgen.small_infrastructure()
    if steps==None:
        steps = 10
    for t in range(steps):
        info(" - now at step {0}".format(t))

    

if __name__ == "__main__":
    run()
