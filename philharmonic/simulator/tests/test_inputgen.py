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

def test_normal_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    events = normal_vmreqs(start, end)
    assert_is_instance(events, pd.TimeSeries)
    for t in events.index:
        assert_greater(t, start)
        assert_less(t, end)
