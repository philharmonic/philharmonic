from nose.tools import *
import pandas as pd

from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def test_fbf_simple_simulated_environment():
    times = range(5)
    env = FBFSimpleSimulatedEnvironment(times)
    times2 = [t for t in env.itertimes()]
    assert_equals(times, times2)
    times_get_time = [env.get_time() for t in env.itertimes()]
    assert_equals(times, times_get_time)

def test_fbf_simple_simulated_environment_series():
    times = pd.date_range('1789-07-14', periods=17, freq='H')
    times_list = [t for t in times]
    env = FBFSimpleSimulatedEnvironment(times)
    times2 = [t for t in env.itertimes()]
    assert_equals(times_list, times2)
    times_get_time = [env.get_time() for t in env.itertimes()]
    assert_equals(times_list, times_get_time)
