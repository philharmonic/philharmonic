from nose.tools import *

from philharmonic.scheduler.generic.fbf_optimiser import FBFOptimiser

def test_fbf_optimiser():
    opt = FBFOptimiser()
    schedule = opt.find_solution()
    assert_is_instance(schedule)
