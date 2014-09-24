from nose.tools import *
import pandas as pd

from philharmonic import Server, VM, Cloud
from philharmonic.simulator.inputgen import *

def test_small_infrastructure():
    cloud = small_infrastructure()
    assert_is_instance(cloud, Cloud)
    servers = cloud.servers
    assert_is_instance(servers, list)
    assert_is_instance(servers[0], Server)

def test_VMRequest():
    e = VMRequest(VM(20,20), 'boot')
    assert_is_instance(e, VMRequest)

def test_within_cloud_capacity():
    assert_true(within_cloud_capacity({'r1': 5, 'r2': 10},
                                      {'r1': 2, 'r2': 3}, 0.5))
    assert_false(within_cloud_capacity({'r1': 5, 'r2': 10},
                                       {'r1': 4, 'r2': 3}, 0.5))
def test_normal_sample():
    value = normal_sample(0, 1, False)
    assert_greater_equal(value, 0)
    assert_is_instance(value, float)
    value = normal_sample(0, 5, True)
    assert_greater_equal(value, 0)
    assert_is_instance(value, int)

def test_auto_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    cloud = small_infrastructure()
    events = auto_vmreqs(start, end, servers=cloud.servers)
    assert_is_instance(events, pd.TimeSeries)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)

def test_normal_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    events = normal_vmreqs(start, end)
    assert_is_instance(events, pd.TimeSeries)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)
