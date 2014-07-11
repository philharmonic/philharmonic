from nose.tools import *
from mock import MagicMock
import pandas as pd

from philharmonic import Schedule
from philharmonic.scheduler import BFDScheduler
from philharmonic.scheduler.bfd_scheduler import sort_vms_decreasing, \
    sort_pms_increasing
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic.simulator.simulator import FBFSimulator
from philharmonic import inputgen, Cloud, VMRequest, VM, Server, State

def test_bfd_returns_schedule():
    scheduler = BFDScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_bfd_reevaluate_initial_placement():
    scheduler = BFDScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    s1, s2 = Server(8000, 4), Server(4000, 2)
    vm1 = VM(2000, 1)
    vm2 = VM(1000, 2)
    vm3 = VM(2000, 2)
    cloud = Cloud([s1, s2], [vm1, vm2, vm3])
    scheduler.cloud = cloud
    r1 = VMRequest(vm1, 'boot')
    r2 = VMRequest(vm2, 'boot')
    r3 = VMRequest(vm3, 'boot')
    scheduler.environment.get_requests = MagicMock(return_value = [r1, r2, r3])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()
    #import ipdb; ipdb.set_trace()
    #assert location of vms
    assert_true(current.all_allocated())
    assert_true(current.all_within_capacity())
    assert_equals(current.allocation(vm1), s1)
    assert_equals(current.allocation(vm2), s1)
    assert_equals(current.allocation(vm3), s2)

def test_sort_vms_decreasing():
    vm1 = VM(2000, 1)
    vm2 = VM(3000, 2)
    vm3 = VM(3000, 4)
    vm4 = VM(1000, 8)
    sorted_vms = sort_vms_decreasing([vm1, vm2, vm3, vm4])
    assert_equals(sorted_vms, [vm4, vm3, vm2, vm1])

def test_sort_empty_pms_increasing():
    pm1 = Server(2000, 1)
    pm2 = Server(3000, 2)
    pm3 = Server(3000, 4)
    pm4 = Server(3000, 1)
    servers = [pm1, pm2, pm3, pm4]
    state = State(servers, [])
    sorted_pms = sort_pms_increasing([pm1, pm2, pm3, pm4], state)
    assert_equals(sorted_pms, [pm1, pm4, pm2, pm3])

def test_sort_nonempty_pms_increasing():
    pm1 = Server(2000, 1)
    pm2 = Server(3000, 2)
    pm3 = Server(3000, 4)
    pm4 = Server(3000, 1)
    vm1 = VM(2000, 1)
    servers = [pm1, pm2, pm3, pm4]
    VMs = [vm1]
    state = State(servers, VMs)
    state.place(vm1, pm4)
    sorted_pms = sort_pms_increasing([pm1, pm2, pm3, pm4], state)
    assert_equals(sorted_pms, [pm4, pm1, pm2, pm3])

    state.remove(vm1, pm4)
    state.place(vm1, pm3)
    sorted_pms = sort_pms_increasing([pm1, pm2, pm3, pm4], state)
    assert_equals(sorted_pms, [pm1, pm4, pm2, pm3])

# TODO: test when initially three VMs are placed and afterwards
# one of them is deleted so that the remaining two can be
# consolidated.

# def test_fbf_run():
#     driver = MagicMock()
#     simulator = FBFSimulator()
#     assert_is_instance(simulator.scheduler, FBFScheduler)
#     simulator.driver = driver
#     times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
#     requests = [VMRequest(VM(2,1), 'boot'), VMRequest(VM(4,2), 'boot')]
#     t1 = pd.Timestamp('2013-02-25 00:00')
#     t2 = pd.Timestamp('2013-02-25 01:00')
#     request_times = [t1, t2]
#     request_series = pd.TimeSeries(requests, request_times)
#     env = FBFSimpleSimulatedEnvironment(times, request_series)
#     simulator.environment = env
#     simulator.cloud = inputgen.small_infrastructure()
#     simulator.arm()
#     assert_is_instance(simulator.scheduler.environment,
#                        FBFSimpleSimulatedEnvironment)
#     simulator.run()
#     assert_true(simulator.driver.apply_action.called)
