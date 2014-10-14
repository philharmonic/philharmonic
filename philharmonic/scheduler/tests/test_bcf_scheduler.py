from nose.tools import *
from mock import MagicMock
import pandas as pd

from philharmonic import Schedule
from philharmonic.scheduler.bcf_scheduler import *

from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic.simulator.simulator import FBFSimulator
from philharmonic.simulator import inputgen
from philharmonic import Cloud, VMRequest, \
    VM, Server, State, Migration

def test_bcf_returns_schedule():
    scheduler = BCFScheduler()
    scheduler.cloud = Cloud()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

def test_bcf_reevaluate_initial_placement():
    scheduler = BCFScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    s1, s2 = Server(4000, 4), Server(4000, 4)
    s1.loc = 'A'
    s2.loc = 'B'
    vm1 = VM(2000, 1)
    vm2 = VM(1000, 2)
    vm3 = VM(2000, 2)
    cloud = Cloud([s1, s2], [vm1, vm2, vm3])
    scheduler.cloud = cloud
    r1 = VMRequest(vm1, 'boot')
    r2 = VMRequest(vm2, 'boot')
    r3 = VMRequest(vm3, 'boot')
    scheduler.environment.get_requests = MagicMock(return_value = [r1, r2, r3])
    scheduler.environment.t = 1
    #scheduler.environment.get_time = MagicMock(return_value = 1)
    # location B cheaper el. price, temperatures the same
    el = pd.DataFrame({'A': [0.16], 'B': [0.08]}, [1])
    temp = pd.DataFrame({'A': [15], 'B': [15]}, [1])
    scheduler.environment.current_data = MagicMock(return_value = (el, temp))
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()
    #assert location of vms
    assert_true(current.all_allocated())
    assert_true(current.all_within_capacity())
    assert_equals(current.allocation(vm3), s2, 'cheaper location picked first')
    assert_equals(current.allocation(vm2), s2, 'cheaper location picked first')
    assert_equals(current.allocation(vm1), s1, 'when no room, the next best')

def test_bcf_reevaluate_underutilised():
    scheduler = BCFScheduler()
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
    assert_true(current.all_within_capacity())
    assert_equals(current.allocation(vm1), s1)
    assert_equals(current.allocation(vm2), s1)
    assert_true(current.all_allocated())

def test_sort_pms_best_first():
    pm1 = Server(2000, 2, location='B')
    pm2 = Server(4000, 4, location='A')
    pm3 = Server(4000, 4, location='B')
    cost = pd.Series({'A': [0.04], 'B': [0.08], 'C': [0.16]})
    servers = [pm2, pm3, pm1]
    state = State(servers, [])
    sorted_pms = sort_active_pms(servers, state, cost)
    assert_equals(sorted_pms, [pm1, pm2, pm3])

def test_sort_pms_cost_first_same_cost():
    """if costs are equal, check that bigger server returned first"""
    pm1 = Server(2000, 1, location='A')
    pm2 = Server(3000, 1, location='A')
    pm3 = Server(3000, 2, location='A')
    pm4 = Server(3000, 4, location='A')
    cost = pd.Series({'A': [0.08], 'B': [0.08]})
    servers = [pm2, pm1, pm4, pm3]
    state = State(servers, [])
    sorted_pms = sort_inactive_pms(servers, state, cost)
    assert_equals(sorted_pms, [pm4, pm3, pm2, pm1])
