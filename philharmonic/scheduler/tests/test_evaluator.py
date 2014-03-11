from nose.tools import *
import pandas as pd

from ..evaluator import *
from philharmonic import Cloud, Server, VM, Schedule, Migration, inputgen
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def test_calculate_cloud_utilisation():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    s3 = Server(4000, 2)
    servers = [s1, s2, s3]
    cloud = Cloud(servers)
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.start = pd.Timestamp('2010-02-26 8:00')
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a2, t2)
    env.end = pd.Timestamp('2010-02-26 16:00')

    df_util = calculate_cloud_utilisation(cloud, env, schedule)
    assert_true((df_util[s1] == [0., 0.5, 0.5, 0.5]).all())
    assert_true((df_util[s2] == [0., 0., 0.375, 0.375]).all())
    assert_true((df_util[s3] == [0., 0., 0., 0.0]).all())

def test_calculate_cloud_simultaneous_actions():
    s1 = Server(4000, 2)
    cloud = Cloud([s1])
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.start = pd.Timestamp('2011-02-26 8:00')
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2011-02-26 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s1)
    schedule.add(a2, t1)
    env.end = pd.Timestamp('2011-02-26 12:00')

    df_util = calculate_cloud_utilisation(cloud, env, schedule)
    assert_equals(len(df_util[s1]), 3, 'duplicate actions must be combined')
    #assert_true((df_util[s1] == [0., 0.5, 0.5, 0.5]).all())

def test_generate_cloud_power():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util})
    precreate_synth_power(index[0], index[-1], ['s1'])
    power = generate_cloud_power(util)

def test_calculate_cost():
    #import ipdb; ipdb.set_trace()
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')

    idx = inputgen.two_days()
    halflen = len(idx)/2
    power_a = [100] * len(idx)
    power_b = [200] * halflen + [250] * halflen
    power = pd.DataFrame({s1: power_a, s2: power_b}, idx)

    el_prices = inputgen.simple_el()
    cost = calculate_cloud_cost(power, el_prices)
    assert_almost_equals(cost[s1], 0.42318367346938734)
    assert_almost_equals(cost[s2], 0.40907755102040827)

def test_calculate_cost_combined():
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    cloud = Cloud(servers)
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.start = pd.Timestamp('2013-02-25 8:00')
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2013-02-25 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2013-02-25 13:00')
    schedule.add(a2, t2)
    env.end = pd.Timestamp('2013-02-25 16:00')

    el_prices = inputgen.simple_el()

    precreate_synth_power(env.start, env.end, servers)

    cost = combined_cost(cloud, env, schedule, el_prices)
    assert_is_instance(cost, float)

    normalised = normalised_combined_cost(cloud, env, schedule, el_prices)
    assert_true(0 <= normalised <= 1.)

def test_calculate_constraint_penalties():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(4000, 2)
    s3 = Server(8000, 4)
    servers = [s1, s2, s3]
    # some VMs
    vm1 = VM(2000, 2);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    cloud = Cloud(servers, VMs, auto_allocate=False)

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.start = pd.Timestamp('2010-02-26 8:00')
    env.end = pd.Timestamp('2010-02-27 8:00')

    # no constraint broken...
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 8:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    schedule.add(a2, t1)

    constraint_penalty = calculate_constraint_penalties(cloud, env, schedule)
    assert_equals(constraint_penalty, 0.)

    # broken constraints...
    a3 = Migration(vm2, s1)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a3, t2)

    constraint_penalty = calculate_constraint_penalties(cloud, env, schedule)
    assert_not_equal(constraint_penalty, 0.)
    #TODO: tests for different constraint violations

def test_calculate_sla_penalties():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(4000, 2)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 2);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs, auto_allocate=False)

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.start = pd.Timestamp('2010-02-26 8:00')
    env.end = pd.Timestamp('2010-02-27 8:00')

    # only 1 migration per VM...
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 8:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-26 10:00')
    schedule.add(a2, t2)

    sla_penalty = calculate_sla_penalties(cloud, env, schedule)
    assert_equals(sla_penalty, 0.)

    # more migrations per VM...
    schedule = Schedule()
    a2 = Migration(vm1, s2)
    for i in range(48):
        if i % 2 == 0:
            action = a1
        else:
            action = a2
        schedule.add(action, t1)
        t1 += pd.offsets.Minute(30)
    sla_penalty = calculate_sla_penalties(cloud, env, schedule)
    assert_almost_equals(sla_penalty, 0.16666666666666666)
