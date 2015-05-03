from nose.tools import *
from mock import MagicMock

from philharmonic import Schedule, Server, VM, VMRequest, Cloud, Migration
import pandas as pd
from philharmonic.scheduler import BruteForceScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment, \
    GASimpleSimulatedEnvironment
from philharmonic.simulator import inputgen
from philharmonic.scheduler import evaluator

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
    scheduler._evaluate_schedule = MagicMock(return_value = 0.5)
    scheduler.cloud = Cloud()
    scheduler.cloud.vms = ['vm1']
    scheduler.cloud.servers = ['s1']
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_brute_force_run():
    mock_schedule_frequency_scaling = MagicMock(return_value = None)
    scheduler = BruteForceScheduler()
    scheduler.no_temperature = False
    scheduler.no_el_price = False
    scheduler._evaluate_schedule = MagicMock(return_value = 0.5)
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 01:00')
    t3 = pd.Timestamp('2013-02-25 02:00')
    request_times = [t1, t2]
    times = [t1, t2, t3]
    scheduler.environment = FBFSimpleSimulatedEnvironment(times=times,
                                                          forecast_periods=1)
    s1, s2 = Server(40000, 12, location='A'), Server(20000, 10, location='A')
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    r2 = VMRequest(vm2, 'boot')
    cloud = Cloud([s1, s2], [vm1, vm2])
    scheduler.cloud = cloud
    scheduler.environment.get_requests = MagicMock(return_value = [r2])
    el = pd.DataFrame({'A': [0.08], 'B': [0.08]}, times)
    temp = pd.DataFrame({'A': [15], 'B': [15]}, times)
    scheduler.environment.current_data = MagicMock(return_value = (el, temp))
    # the initial state is a VM hosted on an underutilised PM
    cloud.apply_real(Migration(vm1, s2))
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()

def test_evaluate_schedule():
    schedule = Schedule()
    scheduler = BruteForceScheduler()
    scheduler.no_temperature = False
    scheduler.no_el_price = False

    # cloud
    vm1 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    servers = [server1, server2]
    scheduler.cloud = Cloud(servers, [vm1])

    # actions
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    times = [t1, t2]
    actions = [Migration(vm1, server1), Migration(vm1, server2)]
    schedule.actions = pd.Series(actions, times)

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = t1
    env.el_prices = inputgen.simple_el()
    env.temperature = inputgen.simple_temperature()
    scheduler.environment = env

    evaluator.precreate_synth_power(env.start, env.end, servers)
    fitness = scheduler._evaluate_schedule(schedule)
    assert_is_instance(fitness, float)

    t3 = pd.Timestamp('2013-02-25 20:00')
    schedule2 = Schedule()
    schedule2.actions = pd.Series(actions, [t1, t3])
    fitness2 = scheduler._evaluate_schedule(schedule2)
    assert_true(fitness < fitness2,
                'schedule migrates to cheaper location earlier')
