from nose.tools import *
from mock import MagicMock
import pandas as pd

from philharmonic import Schedule
from philharmonic.scheduler import FBFScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic.simulator.simulator import FBFSimulator
from philharmonic import inputgen, Cloud

def test_fbf_returns_schedule():
    scheduler = FBFScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_fbf_run():
    driver = MagicMock()
    simulator = FBFSimulator()
    assert_is_instance(simulator.scheduler, FBFScheduler)
    simulator.driver = driver
    times = pd.date_range('2013-02-25', periods=48, freq='H')
    env = FBFSimpleSimulatedEnvironment(times)
    simulator.environment = env
    simulator.cloud = Cloud(servers=inputgen.small_infrastructure())
    simulator.arm()
    assert_is_instance(simulator.scheduler.environment,
                       FBFSimpleSimulatedEnvironment)
    simulator.run()
    #TODO: assert this with deterministic requests
    #assert_true(simulator.driver.apply_action.called)


