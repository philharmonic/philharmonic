from nose.tools import *
import pandas as pd

from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic import *

def test_fbf_simple_simulated_environment_series():
    times = pd.date_range('1789-07-14', periods=17, freq='H')
    times_list = [t for t in times]
    env = FBFSimpleSimulatedEnvironment(times)
    times2 = [t for t in env.itertimes()]
    assert_equals(times_list, times2)
    times_get_time = [env.get_time() for t in env.itertimes()]
    assert_equals(times_list, times_get_time)

def test_fbf_get_requests():
    times = pd.date_range('1789-07-14', periods=17, freq='H')
    env = FBFSimpleSimulatedEnvironment(times)
    env_iter = env.itertimes()
    t = env_iter.next()
    requests = env.get_requests()
    assert_is_instance(requests, pd.Series)

def test_environment_simultaneous_boot_delete():
    times = [pd.Timestamp('2003-01-01 01:00')] * 3
    vm1 = VM(2000, 1)
    vm2 = VM(4000, 2)
    requests_raw = [VMRequest(vm1, 'boot'), VMRequest(vm1, 'delete'),
                    VMRequest(vm2, 'boot')]
    requests = pd.TimeSeries(requests_raw, times)
    env = FBFSimpleSimulatedEnvironment(times, requests)
    env.set_time(times[0])
    env.set_period(pd.offsets.Hour(1))
    #env_iter = env.itertimes()
    #t = env_iter.next()
    requests = env.get_requests()
    assert_equals(set(requests.values), set(requests_raw[2:]))
