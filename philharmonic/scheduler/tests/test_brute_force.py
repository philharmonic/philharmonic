from nose.tools import *
from mock import MagicMock

from philharmonic import Schedule, Server, VM, VMRequest, Cloud, Migration
import pandas as pd
from philharmonic.scheduler import BruteForceScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def test_brute_force_returns_schedule():
    scheduler = BruteForceScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    scheduler.cloud = MagicMock()
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_brute_force_run():
    mock_schedule_frequency_scaling = MagicMock(return_value = None)
    scheduler = BruteForceScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    s1, s2 = Server(40000, 12, location='A'), Server(20000, 10, location='A')
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    r2 = VMRequest(vm2, 'boot')
    cloud = Cloud([s1, s2], [vm1, vm2])
    scheduler.cloud = cloud
    scheduler.environment.get_requests = MagicMock(return_value = [r2])
    scheduler.environment.t = 1
    el = pd.DataFrame({'A': [0.08], 'B': [0.08]}, [1])
    temp = pd.DataFrame({'A': [15], 'B': [15]}, [1])
    scheduler.environment.current_data = MagicMock(return_value = (el, temp))
    # the initial state is a VM hosted on an underutilised PM
    cloud.apply_real(Migration(vm1, s2))
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()
