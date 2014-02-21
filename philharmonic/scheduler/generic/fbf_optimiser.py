import pandas as pd

from optimiser import Optimiser
import philharmonic as ph
from philharmonic import Schedule

def better(pm1, pm2, vm):
    """return better of the two physical machines for hosting vm"""
    #diff = lambda spec,  : 
    #remains_pm1 = 

class FBFOptimiser(Optimiser):
    """First-best-fit schedule optimiser. Goes through the available servers
    to find the first one able to fit target VM s.t. minimum "unused" resources
    remain.

    """
    def __init__(self, infrastructure):
        self.infrastructure = infrastructure
    def find_solution(self, known_data=None, new_requests=pd.TimeSeries([])):
        """return a schedule that's suggested based on the current
        infrastructure availability and the provided @param known_data

        """
        # ph.debug(' - scheduling')
        # ph.debug(new_requests)
        # for request in new_requests: # find a place for each new VM
        #     best_fit = None
        #     for server in self.infrastructure: # check out all the servers
        #         best_fit = better(best_fit, server, request.vm)
        schedule = Schedule()
        return schedule
