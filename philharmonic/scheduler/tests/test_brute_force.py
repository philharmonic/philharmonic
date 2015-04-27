from nose.tools import *
from mock import MagicMock

from philharmonic import Schedule, Server, VM, VMRequest, Cloud, Migration
import pandas as pd
from philharmonic.scheduler import BruteForceScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def test_brute_force_returns_schedule():
    scheduler = BruteForceScheduler()
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 01:00')
    t3 = pd.Timestamp('2013-02-25 02:00')
    scheduler.environment = FBFSimpleSimulatedEnvironment(times=[t1, t2, t3],
                                                          forecast_periods=1)
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(
        return_value = pd.Timestamp('2013-02-25 00:00')
    )
    scheduler.cloud = Cloud()
    scheduler.cloud.vms = ['vm1']
    scheduler.cloud.servers = ['s1']
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_brute_force_run():
    mock_schedule_frequency_scaling = MagicMock(return_value = None)
    scheduler = BruteForceScheduler()
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 01:00')
    t3 = pd.Timestamp('2013-02-25 02:00')
    request_times = [t1, t2]
    scheduler.environment = FBFSimpleSimulatedEnvironment(times=[t1, t2, t3],
                                                          forecast_periods=1)
    s1, s2 = Server(40000, 12, location='A'), Server(20000, 10, location='A')
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    r2 = VMRequest(vm2, 'boot')
    cloud = Cloud([s1, s2], [vm1, vm2])
    scheduler.cloud = cloud
    scheduler.environment.get_requests = MagicMock(return_value = [r2])
    el = pd.DataFrame({'A': [0.08], 'B': [0.08]}, [1])
    temp = pd.DataFrame({'A': [15], 'B': [15]}, [1])
    scheduler.environment.current_data = MagicMock(return_value = (el, temp))
    # the initial state is a VM hosted on an underutilised PM
    cloud.apply_real(Migration(vm1, s2))
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()
