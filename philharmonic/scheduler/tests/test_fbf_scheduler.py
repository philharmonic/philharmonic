from nose.tools import *
from mock import MagicMock
import pandas as pd

from philharmonic import Schedule
from philharmonic.scheduler import FBFScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic.simulator.simulator import FBFSimulator#, Simulator
from philharmonic.simulator import inputgen
from philharmonic import Cloud, VMRequest, VM

def test_fbf_returns_schedule():
    scheduler = FBFScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    scheduler.cloud = MagicMock()
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_fbf_run():
    driver = MagicMock()
    simulator = FBFSimulator() #Simulator() #FBFSimulator()
    assert_is_instance(simulator.scheduler, FBFScheduler)
    simulator.driver = driver
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    requests = [VMRequest(VM(2,1), 'boot'), VMRequest(VM(4,2), 'boot')]
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 01:00')
    request_times = [t1, t2]
    request_series = pd.Series(requests, request_times)
    env = FBFSimpleSimulatedEnvironment(times, request_series)
    simulator.environment = env
    simulator.cloud = inputgen.small_infrastructure()
    simulator.arm()
    assert_is_instance(simulator.scheduler.environment,
                       FBFSimpleSimulatedEnvironment)
    simulator.run()
    assert_true(simulator.driver.apply_action.called)
