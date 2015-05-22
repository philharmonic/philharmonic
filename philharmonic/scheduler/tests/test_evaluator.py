import copy

from nose.tools import *
from mock import patch
import pandas as pd

from ..evaluator import *
from ..evaluator import _server_freqs_to_vm_freqs
from philharmonic import Cloud, Server, VM, Schedule, Migration, \
    IncreaseFreq, DecreaseFreq
from philharmonic.simulator import inputgen
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def _configure(mock_conf):
    mock_conf.f_max = 3000
    mock_conf.f_min = 1000
    mock_conf.f_base = 1000
    mock_conf.C_base = 0.0520278
    mock_conf.C_dif_cpu = 0.018
    mock_conf.C_dif_ram = 0.025
    mock_conf.pricing_model = "perceived_perf_pricing"
    mock_conf.freq_scale_max = 1.0
    mock_conf.freq_scale_min = 0.7
    mock_conf.freq_scale_delta = 0.1
    mock_conf.freq_scale_digits = 1
    mock_conf.power_freq_model = True
    mock_conf.power_model = "freq"
    mock_conf.utilisation_weights = None
    mock_conf.power_weights = None
    mock_conf.P_idle = 100
    mock_conf.P_std = 5
    mock_conf.P_dif = 15
    mock_conf.P_base = 150
    mock_conf.power_freq = '5min'
    mock_conf.pricing_freq = '1h'
    return mock_conf

def test_calculate_cloud_utilisation():
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    s3 = Server(4000, 2)
    servers = [s1, s2, s3]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-26 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = times[0]
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a2, t2)

    df_util = calculate_cloud_utilisation(cloud, env, schedule)
    assert_true((df_util[s1] == [0., 0.5, 0.5, 0.5]).all())
    assert_true((df_util[s2] == [0., 0., 0.375, 0.375]).all())
    assert_true((df_util[s3] == [0., 0., 0., 0.0]).all())

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_cloud_frequencies(mock_conf):
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    s3 = Server(4000, 2)
    servers = [s1, s2, s3]
    cloud = Cloud(servers)

    times = pd.date_range('2010-02-26 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = times[0]
    schedule = Schedule()
    a1 = DecreaseFreq(s1)
    t1 = pd.Timestamp('2010-02-26 11:00')
    schedule.add(a1, t1)
    a2 = DecreaseFreq(s2)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a2, t2)

    f_max = 3000.
    f_lower = 2700.
    mock_conf.f_max = f_max
    freq = calculate_cloud_frequencies(cloud, env, schedule)
    assert_is_instance(freq, pd.DataFrame)
    assert_true((freq[s1] == [f_max] + [f_lower] * 3).all())
    assert_true((freq[s2] == [f_max] * 2 + [f_lower] * 2).all())
    assert_true((freq[s3] == [f_max] * 4).all())

def test_calculate_cloud_simultaneous_actions():
    s1 = Server(4000, 2)
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    cloud = Cloud([s1], set([vm1, vm2]))

    env = FBFSimpleSimulatedEnvironment()
    env.period = pd.offsets.Hour(1)
    env.forecast_periods = 24
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

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_cloud_active_cores(mock_conf):
    # some servers
    s1 = Server(4000, 2)
    s2 = Server(8000, 4)
    s3 = Server(4000, 2)
    servers = [s1, s2, s3]
    cloud = Cloud(servers)

    times = pd.date_range('2010-02-26 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = times[0]
    schedule = Schedule()
    a1 = DecreaseFreq(s1)
    t1 = pd.Timestamp('2010-02-26 11:00')
    schedule.add(a1, t1)
    a2 = DecreaseFreq(s2)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a2, t2)

    f_max = 3000.
    f_lower = 2700.
    mock_conf.f_max = f_max
    active_cores = calculate_cloud_active_cores(cloud, env, schedule)
    assert_is_instance(active_cores, pd.DataFrame)
    # assert_true((freq[s1] == [f_max] + [f_lower] * 3).all())
    # assert_true((freq[s2] == [f_max] * 2 + [f_lower] * 2).all())
    # assert_true((freq[s3] == [f_max] * 4).all())

def test_generate_cloud_power():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util})
    precreate_synth_power(index[0], index[-1], ['s1'])
    power = generate_cloud_power(util)

@patch('philharmonic.scheduler.evaluator.conf')
def test_generate_cloud_power_multicore(mock_conf):
    mock_conf = _configure(mock_conf)
    mock_conf.power_model = "multicore"
    mock_conf.power_weights = [1.318, 0.03559, 0.2243, -0.003184, 0.03137, 0.0004377, 0.007106]
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util})
    precreate_synth_power(index[0], index[-1], ['s1'])
    active_cores = pd.Series([0] * num + [2] * num, index)
    active_cores = pd.DataFrame({'s1': active_cores})
    max_cores = pd.Series([4] * 2 * num, index)
    max_cores = pd.DataFrame({'s1': max_cores})
    power = generate_cloud_power(
        util, power_model="multicore", active_cores=active_cores,
        max_cores=max_cores
    )

def test_calculate_cost():
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
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule.add(a2, t2)

    el_prices = inputgen.simple_el(start=env.t)
    temperature = inputgen.simple_temperature(start=env.t)

    precreate_synth_power(env.start, env.end, servers)

    cost = combined_cost(cloud, env, schedule, el_prices,
                         temperature, env.t, env.forecast_end)
    assert_is_instance(cost, float)

    normalised = normalised_combined_cost(cloud, env, schedule, el_prices,
                                          temperature, env.t, env.forecast_end)
    assert_true(0 <= normalised <= 1.)

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_cost_combined_multicore(mock_conf):
    mock_conf = _configure(mock_conf)
    mock_conf.power_model = "multicore"
    mock_conf.utilisation_weights = [-1.362, 2.798, 1.31, 2.8]
    mock_conf.power_weights = [1.318, 0.03559, 0.2243, -0.003184, 0.03137,
                               0.0004377, 0.007106]
    mock_conf.freq_abs_min = 1800.
    mock_conf.freq_abs_delta = 200
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule.add(a2, t2)

    el_prices = inputgen.simple_el(start=env.t)
    temperature = inputgen.simple_temperature(start=env.t)

    precreate_synth_power(env.start, env.end, servers)
    cost_mc = combined_cost(cloud, env, schedule, el_prices,
                            temperature, env.t, env.forecast_end,
                            power_model="multicore")
    assert_is_instance(cost_mc, float)

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_cost_combined_different_freq(mock_conf):
    mock_conf = _configure(mock_conf)
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule1 = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule1.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule1.add(a2, t2)

    # same as 1, but with lower frequencies
    schedule2 = copy.copy(schedule1)
    schedule2.add(DecreaseFreq(s1), t1)
    schedule2.add(DecreaseFreq(s2), t1)

    # same as 2, but with further decreased frequencies
    # - to test that actions can be chained
    schedule3 = copy.copy(schedule2)
    schedule3.add(DecreaseFreq(s2), t1)
    schedule3.add(DecreaseFreq(s2), t1)
    schedule3.add(DecreaseFreq(s1), t1)
    schedule3.add(DecreaseFreq(s1), t1)

    el_prices = inputgen.simple_el(start=env.t)
    temperature = inputgen.simple_temperature(start=env.t)

    cost1 = combined_cost(cloud, env, schedule1, el_prices,
                          temperature, env.t, env.forecast_end)

    cost2 = combined_cost(cloud, env, schedule2, el_prices,
                          temperature, env.t, env.forecast_end)
    cost3 = combined_cost(cloud, env, schedule3, el_prices,
                          temperature, env.t, env.forecast_end)

    assert_greater(cost1, cost2)
    assert_greater(cost2, cost3)

    normalised1 = normalised_combined_cost(cloud, env, schedule1, el_prices,
                                          temperature, env.t, env.forecast_end)
    normalised2 = normalised_combined_cost(cloud, env, schedule2, el_prices,
                                           temperature, env.t, env.forecast_end)
    normalised3 = normalised_combined_cost(cloud, env, schedule3, el_prices,
                                           temperature, env.t, env.forecast_end)
    assert_true(0 <= normalised3 < normalised2 < normalised1 <= 1.)

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_combined_energy_different_freq(mock_conf):
    mock_conf = _configure(mock_conf)
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule1 = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule1.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule1.add(a2, t2)

    # same as 1, but with lower frequencies
    schedule2 = copy.copy(schedule1)
    schedule2.add(DecreaseFreq(s1), t1)
    schedule2.add(DecreaseFreq(s2), t1)

    # same as 2, but with further decreased frequencies
    # - to test that actions can be chained
    schedule3 = copy.copy(schedule2)
    schedule3.add(DecreaseFreq(s2), t1)
    schedule3.add(DecreaseFreq(s2), t1)
    schedule3.add(DecreaseFreq(s1), t1)
    schedule3.add(DecreaseFreq(s1), t1)

    temperature = inputgen.simple_temperature(start=env.t)

    energy1 = combined_energy(cloud, env, schedule1,
                              temperature, env.t, env.forecast_end)

    energy2 = combined_energy(cloud, env, schedule2,
                          temperature, env.t, env.forecast_end)
    energy3 = combined_energy(cloud, env, schedule3,
                          temperature, env.t, env.forecast_end)

    assert_greater(energy1, energy2)
    assert_greater(energy2, energy3)

def test_server_freqs_to_vm_freqs():
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    servers = [s1, s2]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    cloud = Cloud(servers, VMs)

    cloud.apply(Migration(vm1, s1))
    cloud.apply(Migration(vm2, s2))
    cloud.apply(DecreaseFreq(s1))
    cloud.apply(DecreaseFreq(s2))
    cloud.apply(DecreaseFreq(s2))

    state = cloud.get_current()
    server_freq = state.freq_scale
    #import ipdb; ipdb.set_trace()
    vm_freq = _server_freqs_to_vm_freqs(state)
    assert_equals(vm_freq, {vm1 : 0.9, vm2 : 0.8})

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_cloud_frequencies_for_vms(mock_conf):
    mock_conf = _configure(mock_conf)
    mock_conf.f_max = 2000

    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    cloud = Cloud(servers, VMs)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)

    schedule = Schedule()
    t1 = pd.Timestamp('2010-02-25 8:00')
    schedule.add(Migration(vm1, s1), t1)
    schedule.add(Migration(vm2, s1), t1)
    schedule.add(DecreaseFreq(s1), t1)
    t2 = pd.Timestamp('2010-02-25 14:00')
    schedule.add(DecreaseFreq(s2), t2)
    schedule.add(DecreaseFreq(s2), t2)
    t3 = pd.Timestamp('2010-02-25 18:00')
    schedule.add(Migration(vm1, s2), t3)
    schedule.add(Migration(vm2, s3), t3)

    vm_freq = calculate_cloud_frequencies(cloud, env, schedule, start=times[0],
                                          end=times[-1], for_vms=True)
    assert_is_instance(vm_freq, pd.DataFrame)
    #                                initial, decr, migr, end
    assert_equals(list(vm_freq[vm1]), [1800, 1800, 1600, 1600])
    assert_equals(list(vm_freq[vm2]), [1800, 1800, 2000, 2000])

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_service_profit(mock_conf):
    mock_conf = _configure(mock_conf)

    s1 = Server(4000, 4, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs, auto_allocate=True)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule1 = Schedule()
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule1.add(Migration(vm1, s1), t1)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule1.add(Migration(vm2, s2), t2)

    # same as 1, but with lower frequencies
    schedule2 = copy.copy(schedule1)
    schedule2.add(DecreaseFreq(s1), t1)
    schedule2.add(DecreaseFreq(s1), t1)

    profit1 = calculate_service_profit(cloud, env, schedule1,
                                     env.t, env.forecast_end)
    assert_is_instance(profit1, float)
    profit2 = calculate_service_profit(cloud, env, schedule2,
                                     env.t, env.forecast_end)

    assert_greater(profit1, profit2)

@patch('philharmonic.scheduler.evaluator.conf')
def test_calculate_service_profit_multicore(mock_conf):
    mock_conf = _configure(mock_conf)
    mock_conf.power_model = "multicore"

    s1 = Server(4000, 4, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 4, location='B')
    servers = [s1, s2, s3]
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs, auto_allocate=True)

    times = pd.date_range('2010-02-25 8:00', '2010-02-26 16:00', freq='H')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    schedule1 = Schedule()
    t1 = pd.Timestamp('2010-02-25 11:00')
    schedule1.add(Migration(vm1, s1), t1)
    t2 = pd.Timestamp('2010-02-25 13:00')
    schedule1.add(Migration(vm2, s2), t2)

    # same as 1, but with lower frequencies
    schedule2 = copy.copy(schedule1)
    schedule2.add(DecreaseFreq(s1), t1)
    schedule2.add(DecreaseFreq(s1), t1)

    profit1 = calculate_service_profit(cloud, env, schedule1,
                                     env.t, env.forecast_end)
    assert_is_instance(profit1, float)
    profit2 = calculate_service_profit(cloud, env, schedule2,
                                     env.t, env.forecast_end)

    assert_greater(profit1, profit2)

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
    env.forecast_periods=24
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

    #TODO: test evaluate method with this

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
    env.forecast_periods = 24
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


def test_calculate_migration_overhead():
    # some servers
    s1 = Server(4, 2, location='A')
    s2 = Server(4, 2, location='B')
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2, 2);
    vm2 = VM(2, 2);
    VMs = set([vm1, vm2])
    cloud = Cloud(servers, VMs, auto_allocate=False)

    times = inputgen.two_days(start='2010-02-26 08:00')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    el_prices = inputgen.simple_el(start=env.t)
    env.el_prices = el_prices

    # 1 migration per VM -> booting
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 8:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-26 10:00')
    schedule.add(a2, t2)

    migration_energy, migration_cost = calculate_migration_overhead(
        cloud, env, schedule)
    assert_equals(migration_energy, 0.)
    assert_equals(migration_cost, 0.)

    # more migrations per VM -> actual migration actions
    schedule = Schedule()
    a2 = Migration(vm1, s2)
    for i in range(24):
        if i % 2 == 0:
            action = a1
        else:
            action = a2
        schedule.add(action, t1)
        t1 += pd.offsets.Hour(1)
    migration_energy, migration_cost = calculate_migration_overhead(
        cloud, env, schedule)
    assert_greater(migration_energy, 0.)
    assert_greater(migration_cost, 0.)


def test_evaluate():
    # some servers
    s1 = Server(4000, 2, location='A')
    s2 = Server(8000, 4, location='B')
    s3 = Server(4000, 2, location='B')
    servers = [s1, s2, s3]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    VMs = [vm1, vm2]
    cloud = Cloud(servers, initial_vms=set(VMs))

    times = inputgen.two_days(start='2010-02-26 00:00')
    env = FBFSimpleSimulatedEnvironment(times, forecast_periods=24)
    el_prices = inputgen.simple_el(start=env.t)
    temperature = inputgen.simple_temperature(start=env.t)
    schedule = Schedule()
    a1 = Migration(vm1, s1)
    t1 = pd.Timestamp('2010-02-26 11:00')
    schedule.add(a1, t1)
    a2 = Migration(vm2, s2)
    t2 = pd.Timestamp('2010-02-26 13:00')
    schedule.add(a2, t2)

    precreate_synth_power(times[0], times[-1], servers)
    util_penalty, cost_penalty, constraint_penalty, sla_penalty = evaluate(
        cloud, env, schedule, el_prices, temperature
    )
    assert_true(0 <= util_penalty <= 1, 'normalised value expected')
    assert_true(0 <= cost_penalty <= 1, 'normalised value expected')
    assert_true(0 <= constraint_penalty <= 1, 'normalised value expected')
    assert_true(0 <= sla_penalty <= 1, 'normalised value expected')
