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
    # assert_is_instance(value, float) can also be int
    value = normal_sample(0, 5, True)
    assert_greater_equal(value, 0)
    assert_is_instance(value, int)

def test_distribution_population():
    values = distribution_population(100, 1, 4, distribution='uniform')
    for i in range(1, 5):
        assert_in(i, values)

def test_auto_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    cloud = small_infrastructure()
    events = auto_vmreqs(start, end, servers=cloud.servers)
    assert_is_instance(events, pd.Series)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)

def test_auto_vmreqs_beta_variation():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    cloud = small_infrastructure()
    events = auto_vmreqs_beta_variation(start, end, servers=cloud.servers)
    assert_is_instance(events, pd.Series)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)
    mean_beta = events.apply(lambda e : e.vm.beta).mean()
    assert_not_equal(mean_beta, 1)

def test_normal_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    events = normal_vmreqs(start, end)
    assert_is_instance(events, pd.Series)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)

def test_uniform_vmreqs_beta_variation():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    events = uniform_vmreqs_beta_variation(start, end)
    assert_is_instance(events, pd.Series)
    for t in events.index:
        assert_greater_equal(t, start)
        assert_less_equal(t, end)
