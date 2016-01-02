from nose.tools import *
from mock import Mock, MagicMock, patch
import numpy as np
import pandas as pd

import philharmonic
from philharmonic.simulator.simulator import *
from philharmonic.simulator.inputgen import small_infrastructure

@patch('philharmonic.simulator.simulator.before_start')
@patch('philharmonic.simulator.simulator.serialise_results')
def test_run(mock_before_start, mock_serialise_results):
    philharmonic._setup('philharmonic.settings.test')
    mock_before_start.return_value = True
    mock_serialise_results.return_value = True
    run(steps=2)

# TODO: repurpose these tests to test new simulator methods
def test_server_locations():#TODO: refactor
    servers = small_infrastructure().servers
    server_locations(servers, ['location_'+str(id(s)) for s in servers])
    assert_equals(servers[0].loc, 'location_'+str(id(servers[0])))
    assert_equals(servers[-1].loc, 'location_'+str(id(servers[-1])))

def test_prepare_known_data():
    n = 10
    all_data = pd.Series(
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
    simulator = NoSchedulerSimulator()
    simulator.run()

#def test_simulator_pp():
#    driver = Mock()
#    cloud = Mock()
#    simulator = PeakPauserSimulator()
#    simulator.run()

def test_simulator_noscheduler_nodriver():
    """no scheduler; driver mock - catches all methods and does nothing"""
    driver = MagicMock()
    factory = Simulator.factory_copy()
    factory['scheduler'] = 'NoScheduler'
    simulator = Simulator(factory)
    # arm driver mock
    simulator.driver = driver
    simulator.arm()
    simulator.run()
    #driver.assert...

def test_simulator_pp_nodriver():
    """peak pauser; driver mock"""
    driver = MagicMock()
    simulator = PeakPauserSimulator()
    assert_is_instance(simulator.scheduler, PeakPauser)
    simulator.driver = driver
    #simulator.arm()
    simulator.run()
    assert_true(simulator.driver.apply_action.called)

from philharmonic.scheduler import GAScheduler
from philharmonic.simulator.environment import GASimpleSimulatedEnvironment

def test_gasimulator_empty_environment():
    """test ga scheduler; empty environmentp"""
    factory = Simulator.factory_copy()
    factory['scheduler'] = "GAScheduler"
    simulator = Simulator(factory)
    env = GASimpleSimulatedEnvironment()
    simulator.environment = env
    env.start = pd.Timestamp('2010-01-01')
    env.end = pd.Timestamp('2010-01-02')
    env._times = []
    simulator.arm()
    #import ipdb; ipdb.set_trace()
    simulator.run()
