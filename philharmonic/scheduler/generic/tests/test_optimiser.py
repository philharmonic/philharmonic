from nose.tools import *
import pandas as pd
from datetime import datetime

from philharmonic.scheduler.generic.fbf_optimiser import FBFOptimiser
from philharmonic import Schedule, VMRequest, VM
from philharmonic.simulator.inputgen import small_infrastructure


def test_fbf_optimiser():
    # just the infrastructure capacity and requests are important,
    # no known_data has to be provided
    infrastructure = small_infrastructure()
    requests = [VMRequest(VM(4,2), 'boot'), VMRequest(VM(4,4), 'boot')]
    req_events = pd.Series({datetime(2013, 12, 12, 13, 0):requests})
    optimiser = FBFOptimiser(infrastructure)
    schedule = optimiser.find_solution(new_requests=req_events)
    assert_is_instance(schedule, Schedule)
