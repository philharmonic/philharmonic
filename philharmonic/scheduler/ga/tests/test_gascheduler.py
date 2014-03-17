from __future__ import absolute_import
from nose.tools import *

import pandas as pd

from ..gascheduler import ScheduleUnit, create_random, GAScheduler
from philharmonic import VM, Server, Cloud, Migration
from philharmonic.simulator.environment import GASimpleSimulatedEnvironment
from philharmonic.simulator import inputgen
from philharmonic.scheduler import evaluator

def test_fitness():
    unit = ScheduleUnit()

    #import ipdb; ipdb.set_trace()
    # cloud
    vm1 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    servers = [server1, server2]
    unit.cloud = Cloud(servers, [vm1])

    # actions
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    times = [t1, t2]
    actions = [Migration(vm1, server1), Migration(vm1, server2)]
    unit.actions = pd.Series(actions, times)

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = t1
    env.el_prices = inputgen.simple_el()
    env.temperature = inputgen.simple_temperature()
    unit.environment = env

    evaluator.precreate_synth_power(env.start, env.end, servers)
    fitness = unit.calculate_fitness()
    assert_is_instance(fitness, float)

    t3 = pd.Timestamp('2013-02-25 20:00')
    unit2 = ScheduleUnit()
    unit2.cloud = unit.cloud
    unit2.actions = pd.Series(actions, [t1, t3])
    unit2.environment = env
    fitness2 = unit2.calculate_fitness()
    assert_true(fitness < fitness2, 'unit migrates to cheaper location faster')

def test_mutation():
    unit = ScheduleUnit()

    # cloud
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    unit.cloud = Cloud([server1, server2], set([vm1, vm2]), auto_allocate=False)

    # actions
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    times = [t1, t2]
    actions = [Migration(vm1, server1), Migration(vm2, server2)]
    unit.actions = pd.Series(actions, times)

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = t1
    env.el_prices = inputgen.simple_el()
    unit.environment = env

    mutated = unit.mutation()
    assert_is_instance(mutated, ScheduleUnit)
    assert_true((unit.actions.values == actions).all(), 'original unchanged')
    assert_true((mutated.actions != unit.actions).any(), 'mutated changed')

def test_crossover():

    # cloud
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    t3 = pd.Timestamp('2013-02-25 20:00')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = t1
    env.el_prices = inputgen.simple_el()

    # unit 1
    unit = ScheduleUnit()
    unit.cloud = Cloud([server1, server2])
    unit.environment = env
    times = [t1, t2]
    actions = [Migration(vm1, server1), Migration(vm2, server1)]
    unit.actions = pd.Series(actions, times)

    # unit 2
    unit2 = ScheduleUnit()
    unit2.cloud = unit.cloud
    unit2.environment = env
    actions2 = [Migration(vm2, server2), Migration(vm1, server2)]
    unit2.actions = pd.Series(actions2, [t2, t3])

    child = unit.crossover(unit2)
    assert_is_instance(child, ScheduleUnit)

    child = unit.crossover(unit2, t=t2)
    assert_is_instance(child, ScheduleUnit)
    assert_true((unit.actions.values == actions).all(), 'original unchanged')
    assert_true((unit2.actions.values == actions2).all(), 'original unchanged')
    assert_equals(unit.actions[0], child.actions[0], '1st half one parent')
    assert_equals(unit2.actions[-1], child.actions[-1], '2nd half other parent')

def test_create_random():
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    t1 = pd.Timestamp('2013-02-25 00:00')
    env.t = t1
    vm1 = VM(4,2)
    vm2 = VM(4,2)

    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    cloud = Cloud([server1, server2], set([vm1, vm2]), auto_allocate=False)

    unit = create_random(env, cloud)
    assert_is_instance(unit, ScheduleUnit)

def test_gascheduler():
    # cloud
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    cloud = Cloud([server1, server2], set([vm1, vm2]), auto_allocate=False)

    # actions
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    times = [t1, t2]

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    env.t = t1
    env.el_prices = inputgen.simple_el()
    env.temperature = inputgen.simple_temperature()

    scheduler = GAScheduler()
    scheduler.generation_num = 2
    scheduler.population_size = 6
    scheduler.recombination_rate = 0.4
    scheduler.mutation_rate = 0.18
    scheduler.cloud = cloud
    scheduler.environment = env # TODO: part of the IScheduler constructor
    scheduler.initialize()
    scheduler.reevaluate()

def test_gascheduler_two_times(): # multiple reevaluation calls
    # cloud
    vm1 = VM(4,2)
    vm2 = VM(4,2)
    server1 = Server(8,4, location="A")
    server2 = Server(8,4, location="B")
    cloud = Cloud([server1, server2], set([vm1, vm2]), auto_allocate=False)

    # actions
    t1 = pd.Timestamp('2013-02-25 00:00')
    t2 = pd.Timestamp('2013-02-25 13:00')
    times = [t1, t2]

    # environment
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    env = GASimpleSimulatedEnvironment(times, forecast_periods=20)
    env.t = t1
    env.el_prices = inputgen.simple_el()
    env.temperature = inputgen.simple_temperature()

    scheduler = GAScheduler()
    scheduler.generation_num = 2
    scheduler.population_size = 6
    scheduler.recombination_rate = 0.4
    scheduler.mutation_rate = 0.18
    scheduler.cloud = cloud
    scheduler.environment = env # TODO: part of the IScheduler constructor
    scheduler.initialize()
    scheduler.reevaluate()

    #TODO: apply actions, propagate time
    env.t = pd.Timestamp('2013-02-25 17:00')
    vm3 = VM(4,2)
    cloud.vms.remove(vm2)
    schedule = scheduler.reevaluate()
    assert_true(len(schedule.actions[:'2013-02-25 16:00']) == 0)

# TODO
def test_update():
    pass

def test_update_empty_schedule():
    schedule = ScheduleUnit()
    schedule.update()
