from nose.tools import *
from mock import MagicMock, patch
import pandas as pd

from philharmonic import Schedule
from philharmonic.scheduler.bcffs_scheduler import *

from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment
from philharmonic.simulator.simulator import FBFSimulator
from philharmonic.simulator import inputgen
from philharmonic import Cloud, VMRequest, \
    VM, Server, State, Migration, Pause

import philharmonic.scheduler.bcffs_scheduler
philharmonic.scheduler.bcffs_scheduler.conf.freq_breaks_after_nonfeasible = True


@patch('philharmonic.scheduler.BCFFSScheduler._schedule_frequency_scaling')
def test_bcffs_returns_schedule(mock_schedule_frequency_scaling):
    mock_schedule_frequency_scaling = MagicMock(return_value = None)
    scheduler = BCFFSScheduler()
    scheduler.cloud = Cloud()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)

@patch('philharmonic.scheduler.BCFFSScheduler._schedule_frequency_scaling')
def test_bcf_reevaluate_underutilised(mock_schedule_frequency_scaling):
    mock_schedule_frequency_scaling = MagicMock(return_value = None)
    scheduler = BCFFSScheduler()
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

@patch('philharmonic.scheduler.evaluator.conf')
def test_bcf_reevaluate_freq_scaling(mock_conf):
    f_max = 3000
    mock_conf.f_max = f_max
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

    scheduler = BCFFSScheduler()
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    scheduler.environment = FBFSimpleSimulatedEnvironment(times)
    s1, s2 = Server(4000, 2, location='A'), Server(4000, 2, location='A')
    vm1 = VM(2000, 1); vm1.beta = 0.1
    vm2 = VM(2000, 1); vm2.beta = 0.1
    cloud = Cloud([s1, s2], [vm1, vm2])
    scheduler.cloud = cloud
    r2 = VMRequest(vm2, 'boot')
    scheduler.environment.get_requests = MagicMock(return_value = [r2])
    # the initial state is NOT a VM hosted on an underutilised PM
    cloud.apply_real(Migration(vm1, s2))
    t = times[0]
    el = pd.DataFrame({'A': [0.08] * len(times),
                       'B': [0.08] * len(times)}, times)
    temp = pd.DataFrame({'A': [15] * len(times), 'B': [15] * len(times)}, times)
    scheduler.environment.current_data = MagicMock(return_value = (el, temp))
    schedule = scheduler.reevaluate()
    for action in schedule.actions:
        cloud.apply_real(action)
    current = cloud.get_current()
    assert_true(current.all_within_capacity())
    assert_equals(current.allocation(vm1), s2)
    assert_equals(current.allocation(vm2), s2)
    assert_true(current.all_allocated())

@patch('philharmonic.settings.base')
def test_bcf_reevaluate_freq_scaling_beta_0(mock_conf):
    f_max = 3000
    mock_conf.f_max = f_max
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

    scheduler = BCFFSScheduler()
    with patch('philharmonic.scheduler.bcffs_scheduler.conf', new=mock_conf), \
         patch('philharmonic.conf', new=mock_conf):
        import philharmonic
        philharmonic._override_model_defaults()
        times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
        scheduler.environment = FBFSimpleSimulatedEnvironment(times)
        s1, s2 = Server(4000, 2, location='A'), Server(4000, 2, location='A')
        vm1 = VM(2000, 1); vm1.beta = 0.
        vm2 = VM(2000, 1); vm2.beta = 0.
        vm3 = VM(1000, 1); vm3.beta = 0.
        cloud = Cloud([s1, s2], [vm1, vm2, vm3])
        scheduler.cloud = cloud
        r2 = VMRequest(vm2, 'boot')
        r3 = VMRequest(vm3, 'boot')
        scheduler.environment.get_requests = MagicMock(return_value = [r2, r3])
        # the initial state is a VM hosted on an underutilised PM
        cloud.apply_real(Migration(vm1, s2))
        #cloud.apply_real(Migration(vm2, s2))
        t = times[0]
        el = pd.DataFrame({'A': [0.08] * len(times),
                           'B': [0.05] * len(times)}, times)
        temp = pd.DataFrame({'A': [15] * len(times),
                             'B': [15] * len(times)}, times)
        scheduler.environment.current_data = MagicMock(
            return_value = (el, temp)
        )
        schedule = scheduler.reevaluate()
        for action in schedule.actions:
            cloud.apply_real(action)
        current = cloud.get_current()
        assert_true(current.all_within_capacity())
        assert_equals(current.allocation(vm1), s2)
        assert_equals(current.allocation(vm2), s2)
        assert_equals(current.allocation(vm3), s1)
        assert_true(current.all_allocated())

        assert_equals(current.freq_scale[s1], mock_conf.freq_scale_min)
        assert_equals(current.freq_scale[s2], mock_conf.freq_scale_min)

def test_sort_pms_by_beta():
    s1 = Server(4000, 4, location='B')
    s2 = Server(4000, 4, location='A')
    s3 = Server(4000, 4, location='B')
    vm1 = VM(2000, 1); vm1.beta = 1.
    vm2 = VM(2000, 1); vm2.beta = 0.1
    vm3 = VM(2000, 1); vm3.beta = 0.2
    servers = [s2, s3, s1]
    #state = State(servers, [vm1, vm2, vm3])
    cloud = Cloud(servers, [vm1, vm2, vm3])
    cloud.apply(Migration(vm1, s1))
    cloud.apply(Migration(vm2, s2))
    state = cloud.apply(Migration(vm3, s2))
    sorted_pms = sort_pms_by_beta(servers, state)
    assert_equals(sorted_pms, [s2, s1, s3])
