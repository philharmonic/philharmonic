from nose.tools import *
import pandas as pd

from ..evaluator import calculate_cloud_utilisation, generate_cloud_power
from philharmonic import Cloud, Server, VM, Schedule, Migration
from philharmonic.simulator.environment import Environment

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

    env = Environment()
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

def test_generate_cloud_power():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util})
    power = generate_cloud_power(util)

