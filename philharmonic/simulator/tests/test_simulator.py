from nose.tools import *
import numpy as np
import pandas as pd

from philharmonic.simulator.simulator import *
from philharmonic.simulator.inputgen import small_infrastructure


def test_run():
    run(steps=3)

def test_server_locations():
    servers = small_infrastructure()
    server_locations(servers, ['location_'+str(s) for s in servers])
    assert_equals(servers[0].loc, 'location_'+str(servers[0]))
    assert_equals(servers[-1].loc, 'location_'+str(servers[-1]))

def test_prepare_known_data():
    n = 10
    all_data = pd.TimeSeries(
        np.random.uniform(size=n),
        pd.date_range('2013-01-01', periods=n, freq='D'))
    known_data, known_data2 = prepare_known_data((all_data, all_data),
                                                 pd.Timestamp('2013-01-03'),
                                                 pd.offsets.Day(2))
    #  1 2 3 4 5 6 7 8
    # |    ^    |
    # known_data
    assert_in(pd.Timestamp('2013-01-01'), known_data.index)
    assert_in(pd.Timestamp('2013-01-05'), known_data.index)
    assert_not_in(pd.Timestamp('2013-01-06'), known_data.index)

from philharmonic.scheduler import NoScheduler

def test_simulator():
    # w/ NoScheduler
    simulator = Simulator(scheduler=NoScheduler())
    simulator.run()
