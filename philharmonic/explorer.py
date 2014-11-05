import itertools

import numpy as np
import pandas as pd

from philharmonic import conf
from philharmonic.simulator.simulator import run
from philharmonic.logger import info
from philharmonic.utils import loc

def _generate_range(min_value, max_value, resolution):
    return np.arange(min_value, max_value + resolution, resolution)

def eq(a, b, eps=0.0001):
    """float equality"""
    return abs(a - b) <= eps

# different domain-specific combination-generating methods

class ParameterSpace(object):
    """represents a space of parameter combinations to explore"""
    def __init__(self):
        """generate all the combinations"""
        raise NotImplementedError
    def apply(combination):
        """apply a single combination"""
        raise NotImplementedError

class GAWeights(ParameterSpace):
    """vary the weights of the genetic algorithm's
    fitness function components

    """
    def __init__(self):
        w_util = _generate_range(conf.w_util_min, conf.w_util_max,
                                 conf.resolution)
        w_cost = _generate_range(conf.w_cost_min, conf.w_cost_max,
                                 conf.resolution)
        w_sla = _generate_range(conf.w_sla_min, conf.w_sla_max, conf.resolution)
        w_constraint = _generate_range(conf.w_constraint_min,
                                       conf.w_constraint_max,
                                       conf.resolution)
        parameter_ranges = [w_util, w_cost, w_sla, w_constraint]
        #len(list(itertools.product(*parameter_ranges)))
        combinations = [combo for combo in itertools.product(*parameter_ranges)\
                        if eq(np.sum(combo), 1.)]
        #return combinations
        cnames = ['w_util', 'w_cost', 'w_sla', 'w_constraint']
        self.combinations = pd.DataFrame(combinations,
                                         columns = cnames)
        #columns = ['w_ct', 'w_q', 'w_up', 'w_cd'])

    def apply(self, combination):
        """update the config with the current combination of parameters"""
        w_util, w_cost, w_sla, w_constraint = combination
        print(w_util, w_cost, w_sla, w_constraint)
        conf.gaconf['w_util'] = w_util
        conf.gaconf['w_cost'] = w_cost
        conf.gaconf['w_sla'] = w_sla
        conf.gaconf['w_constraint'] = w_constraint

class TimeOffsets(ParameterSpace):
    """start the simulation with a time offset (also shifting VM requests)"""
    def __init__(self):
        starts = []
        offsets = []
        self.original_start = conf.start
        self.original_times = conf.times
        latest_start = self.original_start + conf.time_offsets_max
        offset = conf.time_offsets_start
        start = self.original_start + offset
        while start < latest_start:
            starts.append(start)
            offsets.append(offset)
            start = start + conf.time_offsets_step
            offset = start - self.original_start
        self.combinations = pd.DataFrame({'offset': offsets, 'starts': starts})

    def apply(self, combination):
        offset, start = combination
        conf.times = self.original_times + offset
        conf.start = conf.times[0]
        conf.end = conf.times[-1]
        conf.factory['requests_offset'] = offset

def generate_combinations():
    """generate a search space of all the possible combinations"""
    return globals()[conf.parameter_space]()

def _run_simulation():
    results = run()
    return results

def _process_results(all_results, new_results):
    cost = new_results['Total cost ($)']
    all_results['cost'].append(cost)

def _serialise_results(results):
    results.to_pickle(loc('exploration_results.pkl'))

# TODO: maybe this function should be a method of ParameterSpace
def _iterate_run(parameter_space):
    """iterate over all the combinations and run the simulation"""
    combinations = parameter_space.combinations
    all_results = {'cost': []}
    for i in combinations.index:
        info('\n' + '#' * 30 +
             '\nExploration iteration ' +
             '{}/{}\n'.format(i + 1,
                              len(combinations.index)) +
             '#' * 30 + '\n')
        parameter_space.apply(combinations.ix[i])
        new_results = _run_simulation()
        info(new_results)
        _process_results(all_results, new_results)
        results = pd.merge(combinations, pd.DataFrame(all_results),
                           left_index=True, right_index=True)
        _serialise_results(results)
    info('\nResults\n--------\n{}'.format(results))
    return results

def explore():
    """explore different parameters"""
    parameter_space = generate_combinations()
    results = _iterate_run(parameter_space)
