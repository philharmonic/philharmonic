'''
Created on Jul 11, 2013

@author: kermit
'''
import unittest
from nose.tools import *

from philharmonic import *
import pandas as pd

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

def test_state():
    import copy
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

def test_allocation():
    s1 = Server(4000, 2)
    servers = [s1]
    vm1 = VM(2000, 1);
    a = State(servers)
    migr = Migration(vm1, s1)
    b = a.transition(migr)

    assert_not_in(vm1, a.alloc[s1], 'vm1 initially unallocated')
    assert_in(vm1, b.alloc[s1], 'vm1 allocated after the transition')

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

def test_schedule():
    vm1 = VM(2000, 1);
    a1 = Pause(vm1)
    t1 = pd.datetime.now()
    a2 = Unpause(vm1)
    t2 = t1 + pd.offsets.Hour(1)
    schedule = Schedule()
    schedule.add(a2, t2)
    schedule.add(a1, t1)
    assert_equals(
        (schedule.actions == pd.Series({t1: a1, t2: a2})).all(), True)

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
