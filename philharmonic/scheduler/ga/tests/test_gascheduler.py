from __future__ import absolute_import
from nose.tools import *

import pandas as pd
from mock import MagicMock

from ..gascheduler import ScheduleUnit, create_random, GAScheduler
from philharmonic import VM, Server, Cloud, Migration, VMRequest
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

def test_best_satisfies_constraints():
    rfitnesses = [0.5, 1, 0.7]
    constraint_penalties = [0, 0.3, 0]
    population = []
    for rfitness, constraint in zip(rfitnesses, constraint_penalties):
        unit = MagicMock()
        unit.rfitness = rfitness
        unit.constraint = constraint
        population.append(unit)
    scheduler = GAScheduler()
    scheduler.population = population
    best = scheduler._best_satisfies_constraints()
    assert_equals(best.rfitness, 0.7)
    assert_equals(best.constraint, 0)

def test_best_satisfies_constraints():
    rfitnesses = [0.5, 1, 0.7]
    constraint_penalties = [0, 0.3, 0]
    population = []
    for rfitness, constraint in zip(rfitnesses, constraint_penalties):
        unit = MagicMock()
        unit.rfitness = rfitness
        unit.constraint = constraint
        population.append(unit)
    scheduler = GAScheduler()
    scheduler.population = population
    best = scheduler._best_satisfies_constraints()
    assert_equals(best.rfitness, 0.7)
    assert_equals(best.constraint, 0)

def test_best_satisfies_constraints():
    rfitnesses = [0.5, 1, 0.7]
    constraint_penalties = [0, 0.3, 0]
    population = []
    for rfitness, constraint in zip(rfitnesses, constraint_penalties):
        unit = MagicMock()
        unit.rfitness = rfitness
        unit.constraint = constraint
        population.append(unit)
    scheduler = GAScheduler()
    scheduler.population = population
    best = scheduler._best_satisfies_constraints()
    assert_equals(best.rfitness, 0.7)
    assert_equals(best.constraint, 0)

def test_best_satisfies_constraints_none():
    rfitnesses = [0.5, 1, 0.7]
    constraint_penalties = [0.2, 0.3, 0.3]
    population = []
    for rfitness, constraint in zip(rfitnesses, constraint_penalties):
        unit = MagicMock()
        unit.rfitness = rfitness
        unit.constraint = constraint
        population.append(unit)
    scheduler = GAScheduler()
    scheduler.population = population
    best = scheduler._best_satisfies_constraints()
    assert_is(best, None)

def test_add_boot_actions_greedily():
    # some servers
    s1 = Server(4000, 8)
    s2 = Server(8000, 8)
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1);
    vm2 = VM(2000, 2);
    vm3 = VM(2000, 3);
    vms = [vm1, vm2]
    scheduler = GAScheduler()
    scheduler.cloud = Cloud(servers)

    reqs = [VMRequest(vm1, 'boot'), VMRequest(vm2, 'boot'),
            VMRequest(vm3, 'boot')]
    times = pd.date_range('2013-02-25 00:00', periods=48, freq='H')
    environment = GASimpleSimulatedEnvironment(times, forecast_periods=24)
    environment.t = times[0]
    environment.get_requests = MagicMock(return_value=reqs[:2])
    scheduler.environment = environment

    unit = ScheduleUnit()
    unit.environment = environment
    unit.add(reqs[2], environment.t)
    #import ipdb; ipdb.set_trace()
    scheduler._add_boot_actions_greedily(unit)
    expected_action_vms = set([action.vm for action in reqs])
    for action in unit.actions.values:
        assert_in(action.vm, expected_action_vms)

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
    scheduler._create_or_update_population()
    schedule = scheduler.reevaluate()
    assert_true(len(schedule.actions[:'2013-02-25 16:00']) == 0)

# TODO
def test_update():
    pass

def test_update_empty_schedule():
    schedule = ScheduleUnit()
    schedule.update()
