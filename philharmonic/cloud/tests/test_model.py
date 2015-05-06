'''
Created on Jul 11, 2013

@author: kermit
'''
import unittest
from mock import Mock, MagicMock

from nose.tools import *
import pandas as pd

from philharmonic import *
from philharmonic.simulator.environment import Environment

def test_machine_id():
    s1 = Server(4000, 2)
    vm1 = VM(2000, 1)
    s2 = Server(8000, 4)
    vm2 = VM(2000, 2)
    assert_equals(s1.id, 1)
    assert_equals(s2.id, 2)
    assert_equals(vm1.id, 1)
    assert_equals(vm2.id, 2)
    s1_copy = Server(4000, 2)
    s1_copy.id = s1.id
    assert_equals(s1, s1_copy)
    d = {s1: 'bla'}
    assert_true(s1_copy in d)

def test_machine_repr_not_exploding():
    s1 = Server(4000, 2)
    vm1 = VM(2000, 1)
    for m in [s1, vm1]:
        m.full_info()
        m.full_info(location=False)
        repr(m)
        str(m)

def test_constraints():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    a = State(servers, VMs, auto_allocate=False)

    # allocate and check capacity and allocation
    a.place(vm1,s1)
    assert_equals(a.all_within_capacity(), True, 'all servers within capacity')
    assert_almost_equals(a.ratio_within_capacity(), 1.0)
    assert_equals(a.all_allocated(), False, 'not all VMs are allocated')
    #import ipdb; ipdb.set_trace()
    assert_almost_equals(a.ratio_allocated(), 0.5)

    a.place(vm2, s1)
    assert_equals(a.all_within_capacity(), False,
                  'not all servers within capacity')
    assert_almost_equals(a.ratio_within_capacity(), 0.5)
    assert_equals(a.all_allocated(), True, 'all VMs are allocated')
    assert_almost_equals(a.ratio_allocated(), 1.0)

    a.remove(vm2, s1)
    a.place(vm2, s2)
    assert_equals(a.all_within_capacity(), True, 'all servers within capacity')
    assert_almost_equals(a.ratio_within_capacity(), 1.0)
    assert_equals(a.all_allocated(), True, 'all VMs are allocated')
    assert_almost_equals(a.ratio_allocated(), 1.0)

def test_within_capacity():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    a = State(servers, VMs, auto_allocate=False)

    assert_true(a.within_capacity(s1))
    a.place(vm1,s1)
    assert_true(a.within_capacity(s1))
    a.place(vm2,s1)
    assert_false(a.within_capacity(s1))
    assert_true(a.within_capacity(s2))
    a.migrate(vm1, s2)
    assert_true(a.within_capacity(s1))
    assert_true(a.within_capacity(s2))
    a.migrate(vm2, s2)
    assert_true(a.within_capacity(s1))
    assert_true(a.within_capacity(s2))

def test_overcapacitated_servers():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 4)
    s2 = Server(1000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1); vm2 = VM(2000, 2); vm3 = VM(2000, 2);
    VMs = set([vm1, vm2, vm3])
    a = State(servers, VMs, auto_allocate=False)

    # allocate and check capacity
    a.place(vm1,s1)
    assert_sequence_equal(list(a.overcapacitated_servers()), [])
    a.place(vm2, s1)
    assert_sequence_equal(list(a.overcapacitated_servers()), [])
    a.place(vm3, s1)
    assert_sequence_equal(list(a.overcapacitated_servers()), [s1])
    a.migrate(vm3, s2)
    assert_sequence_equal(list(a.overcapacitated_servers()), [s2])

def test_allocation():
    s1 = Server(4000, 2)
    vm1 = VM(2000, 1)
    state = State([s1], [vm1])
    assert_true(state.allocation() is None)
    state.place(vm1, s1)
    assert_true(state.allocation() == s1)

def test_capacity_penalty():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    s2 = Server(4000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 2);
    vm2 = VM(2000, 2);
    vm3 = VM(2000, 2);
    VMs = [vm1, vm2, vm3]
    a = State(servers, VMs)

    # allocate and check capacity and allocation
    a.place(vm1,s1)
    assert_almost_equals(a.capacity_penalty(), 0.0)

    a.place(vm2,s1)
    pen1 = a.capacity_penalty()
    assert_true(pen1 > 0.)
    a.place(vm3, s1)
    pen2 = a.capacity_penalty()
    assert_true(pen2 > 0.)
    assert_true(pen2 > pen1)

def test_capacity_penalty_heterogeneous_resources():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 4)
    servers = [s1]
    # some VMs
    vm1 = VM(2000, 2);
    vm2 = VM(2000, 2);
    vm3 = VM(2000, 2);
    VMs = [vm1, vm2, vm3]
    a = State(servers, VMs)

    # allocate and check capacity and allocation
    a.place(vm1,s1)
    assert_almost_equals(a.capacity_penalty(), 0.0)
    a.place(vm2,s1)
    assert_almost_equals(a.capacity_penalty(), 0.0)
    a.place(vm3, s1)
    pen = a.capacity_penalty()
    assert_almost_equals(pen, 0.5)

def test_capacity_penalty_multiple_violations():
    """test if max_overcap check stops detecting multiple violations"""
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 4)
    s2 = Server(4000, 5)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(3000, 3);
    vm2 = VM(3000, 3);
    vm3 = VM(2100, 3);
    vm4 = VM(2100, 3);
    VMs = [vm1, vm2, vm3, vm4]
    a = State(servers, VMs)

    # allocate and check capacity and allocation
    a.place(vm1,s1)
    assert_almost_equals(a.capacity_penalty(), 0.0)
    a.place(vm2,s1)
    pen1 = a.capacity_penalty()
    assert_greater(pen1, 0.)
    a.place(vm3, s2)
    pen2 = a.capacity_penalty()
    assert_equals(pen1, pen2)
    a.place(vm4, s2)
    pen3 = a.capacity_penalty()
    assert_greater(pen3, pen2)

def test_state():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(1000, 1);
    vm3 = VM(1000, 1);
    VMs = [vm1,vm2,vm3]
    a = State(servers, VMs, auto_allocate=False)
    a.place(vm1, s1)
    a.place(vm2, s2)
    a.place(vm3, s2)
    b = a.copy()
    b.remove(vm1, s1)
    assert_in(vm1, a.alloc[s1], 'changing one state must not affect the other')

def test_state_place_free_cap():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(1000, 1);
    vm3 = VM(1000, 1);
    VMs = [vm1,vm2,vm3]
    a = State(servers, VMs, auto_allocate=False)
    assert_equals(a.free_cap[s1]['RAM'], 4000)
    assert_equals(a.free_cap[s1]['#CPUs'], 2)
    a.place(vm1, s1)
    a.place(vm2, s2)
    a.place(vm3, s2)
    assert_equals(a.free_cap[s1]['RAM'], 2000)
    assert_equals(a.free_cap[s1]['#CPUs'], 1)
    b = a.copy()
    b.remove(vm1, s1)
    assert_equals(a.free_cap[s1]['RAM'], 2000)
    assert_equals(a.free_cap[s1]['#CPUs'], 1)
    assert_equals(b.free_cap[s1]['RAM'], 4000)
    assert_equals(b.free_cap[s1]['#CPUs'], 2)

def test_server_free():
    s1 = Server(4000, 2)
    vm1 = VM(2000, 2)
    state = State([s1], [vm1], auto_allocate=False)
    assert_true(state.server_free(s1))
    state.place(vm1, s1)
    assert_false(state.server_free(s1))

def test_state_change_frequency():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    a = State(servers, [])
    assert_equals(a.freq_scale[s1], 1.)
    assert_equals(a.freq_scale[s2], 1.)
    a.decrease_freq(s1)
    assert_equals(a.freq_scale[s1], 0.9)
    b = a.copy()
    b.decrease_freq(s1)
    assert_equals(a.freq_scale[s1], 0.9)
    assert_equals(b.freq_scale[s1], 0.8)
    c = b.copy()
    c.increase_freq(s1)
    assert_equals(b.freq_scale[s1], 0.8)
    assert_equals(c.freq_scale[s1], 0.9)
    c.increase_freq(s2)
    assert_equals(c.freq_scale[s2], 1.)
    c.freq_scale[s1] = Server.freq_scale_min
    c.decrease_freq(s1)
    assert_equals(c.freq_scale[s1], Server.freq_scale_min)

def test_action_equality():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    VMs = [vm1]

    migr1 = Migration(vm1, s2)
    migr2 = Migration(vm1, s2)
    migr3 = Migration(vm1, s1)
    pause1 = Pause(vm1)
    pause2 = Pause(vm1)
    pause3 = Pause(vm2)
    assert_equals(migr1, migr2)
    migr1 = Migration(vm1, s2)
    migr2 = Migration(vm1, s2)
    assert_not_equals(migr1, migr3)
    assert_not_equals(migr1, pause1)
    assert_equals(pause1, pause2)
    assert_not_equals(pause2, pause3)

def test_migration():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    VMs = [vm1]

    a = State(servers, VMs)
    # initial position
    a.place(vm1, s1)
    migr = Migration(vm1, s2)
    b = a.transition(migr)

    assert_in(vm1, a.alloc[s1], 'vm1 should be on s1 before transition')
    assert_not_in(vm1, a.alloc[s2], 'vm1 should be on s1 before transition')

    assert_not_in(vm1, b.alloc[s1], 'vm1 should have moved after the transition')
    assert_in(vm1, b.alloc[s2], 'vm1 should have moved after the transition')

def test_multiple_state_transitions():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(1000, 1);
    VMs = set()

    a = State(servers, VMs)
    b = a.transition(VMRequest(vm1, 'boot'))
    c = b.transition(Migration(vm1, s1))
    # alternative route
    c2 = b.transition(Migration(vm1, s2))
    d0 = c.transition(VMRequest(vm2, 'boot'))
    d = d0.transition(Migration(vm2, s2))
    # raises error - vm2 not in VMs

    assert_equals(a.vms, set([]))
    assert_equals(b.vms, set([vm1]))

    assert_not_in(vm1, a.alloc[s1])
    assert_not_in(vm1, b.alloc[s1])
    assert_in(vm1, c.alloc[s1])
    assert_not_in(vm1, c.alloc[s2])
    assert_not_in(vm1, c2.alloc[s1])
    assert_in(vm1, c2.alloc[s2])

    assert_not_in(vm2, c2.alloc[s2])
    assert_not_in(vm2, c.alloc[s2])
    assert_in(vm2, d.alloc[s2])

@raises(ModelUsageError)
def test_migrating_unbooted_error():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(1000, 1);
    VMs = set()

    a = State(servers, VMs)
    b = a.transition(Migration(vm1, s1))

def test_vms_during_state_transitions():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    VMs = set()

    a = State(servers, VMs)
    b = a.transition(VMRequest(vm1, 'boot'))
    c = b.transition(Migration(vm1, s1))
    d = c.transition(VMRequest(vm2, 'boot'))
    e = d.transition(VMRequest(vm1, 'delete'))

    assert_equals(a.vms, set([]))
    assert_equals(b.vms, set([vm1]))
    assert_not_in(vm1, b.alloc[s1])
    assert_equals(c.vms, set([vm1]))
    assert_in(vm1, c.alloc[s1])
    assert_equals(d.vms, set([vm1, vm2]))
    assert_equals(e.vms, set([vm2]))
    assert_not_in(vm1, e.alloc[s1])

def test_apply():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    VMs = [vm1]
    cloud = Cloud(servers, VMs)

    initial = cloud.get_current()
    a1 = cloud.apply(Migration(vm1, s1))
    a2 = cloud.apply(Migration(vm1, s2))
    a3 = cloud.apply(Migration(vm1, s1), inplace=True)
    assert_not_equals(a1, a2, "applying by default creates a copy")
    assert_equals(a2, a3, "applying inplace modifies the current state")

def test_apply_real():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    VMs = [vm1]
    cloud = Cloud(servers, VMs)

    a1 = cloud.apply_real(Migration(vm1, s1))
    a2 = cloud.apply_real(Migration(vm1, s2))
    a3 = cloud.apply_real(Migration(vm1, s1), inplace=True)
    assert_not_equals(a1, a2, "applying by default creates a copy")
    assert_equals(a2, a3, "applying inplace modifies the old state")

def test_state_reset():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    VMs = set()
    cloud = Cloud(servers, VMs)

    initial1 = cloud.get_current()
    real1 = cloud.apply_real(VMRequest(vm1, 'boot'))
    current11 = cloud.apply(Migration(vm1, s1))
    current12 = cloud.apply(Migration(vm1, s2))

    cloud.reset_to_real()
    real2 = cloud.apply_real(VMRequest(vm2, 'boot'))
    current21 = cloud.apply(Migration(vm1, s2))
    current22 = cloud.apply(Migration(vm2, s2))

    cloud.reset_to_initial()
    initial2 = cloud.get_current()

    assert_equals(initial1.vms, set([]))
    assert_not_in(vm1, initial1.alloc[s1])
    assert_equals(real1.vms, set([vm1]))
    assert_in(vm1, current11.alloc[s1])
    assert_not_in(vm1, current11.alloc[s2])
    assert_in(vm1, current12.alloc[s2])

    assert_not_in(vm1, real2.alloc[s2])
    assert_equals(real2.vms, set([vm1, vm2]))
    assert_in(vm1, current21.alloc[s2])
    assert_not_in(vm2, current21.alloc[s2])
    assert_in(vm2, current22.alloc[s2])

    assert_equals(initial2.vms, set([]))

def test_state_reset_direct_manipulation():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    VMs = set()
    cloud = Cloud(servers, VMs)

    initial1 = cloud.get_current()
    real1 = cloud.apply_real(VMRequest(vm1, 'boot'))
    # these two states are the same as no copy is made:
    current11 = cloud.get_current().migrate(vm1, s1)
    current12 = cloud.get_current().migrate(vm1, s2)

    cloud.reset_to_real()
    real2 = cloud.apply_real(VMRequest(vm2, 'boot'))
    real2 = cloud.apply_real(Migration(vm1, s1))
    # these two states are the same as no copy is made:
    current21 = cloud.get_current().migrate(vm1, s2)
    current22 = cloud.get_current().migrate(vm2, s2)

    cloud.reset_to_initial()
    initial2 = cloud.get_current()

    assert_equals(initial1.vms, set([]))
    assert_not_in(vm1, initial1.alloc[s1])
    assert_equals(real1.vms, set([vm1]))
    assert_not_in(vm1, real1.alloc[s1], 'real1 must be unchanged')
    assert_not_in(vm1, real1.alloc[s2], 'real1 must be unchanged')
    assert_in(vm1, current11.alloc[s2])
    assert_not_in(vm1, current11.alloc[s1])
    assert_equals(current11, current12)

    assert_equals(real2.vms, set([vm1, vm2]))
    assert_in(vm1, real2.alloc[s1])
    assert_not_in(vm1, real2.alloc[s2])
    assert_not_in(vm2, real2.alloc[s1], 'real2 must be unchanged')
    assert_not_in(vm2, real2.alloc[s2], 'real2 must be unchanged')
    assert_in(vm1, current21.alloc[s2])
    assert_in(vm2, current21.alloc[s2])
    assert_in(vm2, current22.alloc[s2])
    assert_equals(current11, current12)

    assert_equals(initial2.vms, set([]))

def test_state_calculate_prices():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm1.price = 0.2
    vm2 = VM(2000, 1)
    vm2.price = 0.4
    VMs = [vm1, vm2]
    cloud = Cloud(servers, VMs)

    state = cloud.get_current()
    cloud.apply(Migration(vm1, s1), inplace=True)
    cloud.apply(Migration(vm2, s2), inplace=True)
    price1 = pd.Series(state.calculate_prices()).sum()
    cloud.apply(DecreaseFreq(s1), inplace=True)
    cloud.apply(DecreaseFreq(s2), inplace=True)
    cloud.apply(DecreaseFreq(s2), inplace=True)
    price2 = pd.Series(state.calculate_prices()).sum()

    assert_is_instance(price1, float)
    assert_is_instance(price2, float)

def test_migration_free_cap():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    VMs = [vm1]

    a = State(servers, VMs)
    # initial position
    a.place(vm1, s1)
    assert_equals(a.free_cap[s1]['RAM'], 2000)
    migr = Migration(vm1, s2)
    b = a.transition(migr)

    assert_equals(a.free_cap[s1]['RAM'], 2000)
    assert_equals(a.free_cap[s2]['RAM'], 8000)

    assert_equals(b.free_cap[s1]['RAM'], 4000)
    assert_equals(b.free_cap[s2]['RAM'], 6000)

def test_utilisation():
    vm = VM(2000, 1)
    s = Server(20000, 10)
    cloud = Cloud([s], [vm])
    assert_equals(cloud.get_current().utilisation(s), 0)
    cloud.apply(Migration(vm, s))
    assert_equals(cloud.get_current().utilisation(s), 0.1)

def test_underutilised():
    vm = VM(2000, 1)
    vm2 = VM(10000, 8)
    s = Server(20000, 10)
    cloud = Cloud([s], [vm, vm2])
    assert_false(cloud.get_current().underutilised(s))
    cloud.apply(Migration(vm, s))
    assert_true(cloud.get_current().underutilised(s))
    cloud.apply(Migration(vm2, s))
    assert_false(cloud.get_current().underutilised(s))

def test_allocation():
    s1 = Server(4000, 2)
    servers = [s1]
    vm1 = VM(2000, 1);
    a = State(servers, set([vm1]))
    migr = Migration(vm1, s1)
    b = a.transition(migr)

    assert_not_in(vm1, a.alloc[s1], 'vm1 initially unallocated')
    assert_in(vm1, b.alloc[s1], 'vm1 allocated after the transition')

@raises(AttributeError)
def test_alloc_readonly():
    s1 = Server(4000, 2)
    servers = [s1]
    vm1 = VM(2000, 1);
    a = State(servers, set([vm1]))
    a.place(vm1, s1)
    a.alloc = {}

def test_pause():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    VMs = [vm1]

    a = State(servers, VMs)
    # initial position
    a.place(vm1, s1)
    pause = Pause(vm1)
    b = a.transition(pause)

    assert_not_in(vm1, a.paused,
                  'vm1 should not be paused before transition')
    assert_in(vm1, b.paused,
              'vm1 should be paused after transition')

def test_change_frequency():
    # some servers
    s1 = Server(4000, 2)
    servers = [s1]

    a = State(servers)
    decrease = DecreaseFreq(s1)
    b = a.transition(decrease)
    increase = IncreaseFreq(s1)
    c = b.transition(increase)
    assert_equals(a.freq_scale[s1], 1.)
    assert_equals(b.freq_scale[s1], 0.9)
    assert_equals(c.freq_scale[s1], 1.)

def test_schedule():
    vm1 = VM(2000, 1);
    a1 = Pause(vm1)
    t1 = pd.datetime.now()
    a2 = Unpause(vm1)
    t2 = t1 + pd.offsets.Hour(1)
    schedule = Schedule()
    schedule.add(a2, t2)
    schedule.add(a1, t1)
    assert_true((schedule.actions == pd.Series({t1: a1, t2: a2})).all())

def test_schedule_copy():
    vm1 = VM(2000, 1);
    a1 = Pause(vm1)
    t1 = pd.datetime.now()
    a2 = Unpause(vm1)
    t2 = t1 + pd.offsets.Hour(1)
    schedule = Schedule()
    schedule.add(a2, t2)
    schedule.add(a1, t1)
    schedule2 = schedule.copy()
    a3 = Pause(vm1)
    t3 = t1 + pd.offsets.Hour(2)
    schedule2.add(a3, t3)
    assert_true((schedule.actions == pd.Series({t1: a1, t2: a2})).all())
    assert_true(
        (schedule2.actions == pd.Series({t1: a1, t2: a2, t3: a3})).all()
    )

def test_schedule_add_first_replaced():
    vm1 = VM(2000, 1);
    s1 = Server(5000, 2);
    s2 = Server(5000, 2);
    a1 = Migration(vm1, s1)
    a2 = Migration(vm1, s2)
    t1 = pd.datetime.now()
    a3 = Migration(vm1, s2)
    t2 = t1 + pd.offsets.Hour(1)
    schedule = Schedule()
    schedule.add(a1, t1)
    schedule.add(a2, t1)
    schedule.add(a3, t2)
    expected = pd.Series([a1, a2, a3], index=[t1, t1, t2])
    assert_true((schedule.actions == expected).all())

def test_schedule_add_existing():
    vm1 = VM(2000, 1);
    s1 = Server(5000, 2);
    s2 = Server(5000, 2);
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2002-01-01 03:00')
    a2 = Migration(vm1, s2)
    a3 = Migration(vm1, s2)
    t2 = t1 + pd.offsets.Hour(1)
    schedule = Schedule()
    schedule.environment = Environment()
    schedule.environment.period = pd.offsets.Hour(1)
    schedule.add(a2, t2)
    schedule.add(a1, t1)
    schedule.add(a3, t2)
    # TODO: add existing
    assert_true((schedule.actions == pd.Series({t1: a1, t2: a2})).all())

def test_schedule_filter():
    s = Schedule()
    vm1 = VM(2000, 1);
    a1 = Pause(vm1)
    t1 = pd.Timestamp('2013-01-01 00:00')
    a2 = Unpause(vm1)
    t2 = pd.Timestamp('2013-01-01 01:00')
    s.add(a1, t1)
    s.add(a2, t2)
    filtered = s.filter_current_actions(t1, pd.offsets.Hour(1))
    assert_in(a1, filtered.values)
    assert_not_in(a2, filtered.values)

def test_cloud():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs)
    #TODO: test that auto_allocate doesn't break constraints
    assert_equals(cloud.vms, VMs)

def test_schedule_sorted():
    schedule = Schedule()
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    a1 = VMRequest(vm1, 'boot')
    a2 = VMRequest(vm1, 'delete')
    a3 = Migration(vm1, s1)
    a4 = Pause(vm1)
    a5 = Unpause(vm1)
    t1 = pd.Timestamp('2013-01-01 00:00')
    b1 = VMRequest(vm2, 'boot')
    b2 = Migration(vm2, s1)
    t2 = pd.Timestamp('2013-01-01 01:00')
    schedule.add(a3, t1)
    schedule.add(a5, t1)
    schedule.add(a4, t1)
    schedule.add(b2, t2)
    schedule.add(a2, t1)
    schedule.add(b1, t2)
    schedule.add(a1, t1)
    assert_sequence_equal(list(schedule.actions.values),
                          [a1, a2, a3, a4, a5, b1, b2])

def test_hash_action():
    s1 = Server(4000, 2)
    s2 = Server(4000, 2)
    vm1 = VM(2000, 1)
    a1 = Migration(vm1, s1)
    a2 = Migration(vm1, s1)
    a3 = Migration(vm1, s2)
    assert_equals(hash(a1), hash(a2))
    assert_not_equals(hash(a1), hash(a3))

def test_schedule_clean():
    schedule = Schedule()
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    # duplicates
    a01 = VMRequest(vm1, 'boot')
    a02 = VMRequest(vm2, 'boot')
    a1 = Migration(vm1, s1)
    a2 = Migration(vm1, s1)
    t1 = pd.Timestamp('2013-01-01 00:00')
    # same vm & timestamp, different action
    b1 = Migration(vm2, s1)
    b2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2013-01-01 01:00')
    # normal
    c1 = Migration(vm1, s1)
    c2 = Migration(vm2, s1)
    t3 = pd.Timestamp('2013-01-01 02:00')
    times = [t1, t1, t1, t1, t2, t2, t3, t3]
    actions = [a01, a02, a1, a2, b1, b2, c1, c2]
    schedule.actions = pd.TimeSeries(actions, times)
    schedule.clean()
    assert_sequence_equal(list(schedule.actions.values),
                          [a01, a02, a1, b2, c1, c2])

def test_vm_requests():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    vms = [vm1, vm2]
    cloud = Cloud(servers)

    assert_not_in(vm1, cloud.vms, 'vm1 should not be booted')
    assert_not_in(vm2, cloud.vms, 'vm1 should not be booted')
    req = VMRequest(vm1, 'boot')
    cloud.apply(req)
    assert_in(vm1, cloud.vms, 'vm1 should be booted')
    assert_not_in(vm2, cloud.vms, 'vm1 should not be booted')
    cloud.apply(VMRequest(vm1, 'delete'))
    cloud.apply(VMRequest(vm2, 'boot'))
    assert_not_in(vm1, cloud.vms, 'vm1 should be booted')
    assert_in(vm2, cloud.vms, 'vm1 should not be booted')
