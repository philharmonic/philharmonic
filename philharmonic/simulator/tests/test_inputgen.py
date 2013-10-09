from nose.tools import *
import pandas as pd

from philharmonic.scheduler.generic.model import Server, VM
from philharmonic.simulator.inputgen import *

def test_small_infrastructure():
    servers = small_infrastructure()
    assert_is_instance(servers, list)
    assert_is_instance(servers[0], Server)

def test_VMEvent():
    e = VMEvent(VM(20,20), pd.Timestamp('2010-01-15 00:00'), 'boot')
    assert_is_instance(e, VMEvent)
    assert_is_instance(e.t, pd.Timestamp)

def test_normal_vmreqs():
    start = pd.Timestamp('2010-01-01')
    end = pd.Timestamp('2010-01-31')
    events = normal_vmreqs(start, end)
    for event in events:
        assert_greater(event.t, start)
        assert_less(event.t, end)
