import itertools

import numpy as np
import pandas as pd

from philharmonic import conf
from philharmonic.simulator.simulator import run
from philharmonic.logger import info
from philharmonic.utils import loc

def _generate_range(min_value, max_value, resolution):
    return np.arange(min_value, max_value + resolution, resolution)

def _generate_combinations():
    """generate a search space of all the possible combinations"""
    w_util = _generate_range(conf.w_util_min, conf.w_util_max, conf.resolution)
    w_cost = _generate_range(conf.w_cost_min, conf.w_cost_max, conf.resolution)
    w_sla = _generate_range(conf.w_sla_min, conf.w_sla_max, conf.resolution)
    w_constraint = _generate_range(conf.w_constraint_min, conf.w_constraint_max,
                                   conf.resolution)
    parameter_ranges = [w_util, w_cost, w_sla, w_constraint]
    #len(list(itertools.product(*parameter_ranges)))
    combinations = [combo for combo in itertools.product(*parameter_ranges) \
                    if np.sum(combo) == 1.]
    #return combinations
    cnames = ['w_util', 'w_cost', 'w_sla', 'w_constraint']
    combinations = pd.DataFrame(combinations,
                                columns = cnames)
                                #columns = ['w_ct', 'w_q', 'w_up', 'w_cd'])
    return combinations

def _set_config(combination):
    """update the config with the current combination of parameters"""
    w_util, w_cost, w_sla, w_constraint = combination
    print(w_util, w_cost, w_sla, w_constraint)
    conf.gaconf['w_util'] = w_util
    conf.gaconf['w_cost'] = w_cost
    conf.gaconf['w_sla'] = w_sla
    conf.gaconf['w_constraint'] = w_constraint

def _run_simulation():
    results = run()
    return results

def _process_results(all_results, new_results):
    cost = new_results['Total cost ($)']
    all_results['cost'].append(cost)

def _serialise_results(combinations, results):
    data = pd.merge(combinations, results, left_index=True, right_index=True)
    data.to_pickle(loc('exploration_results.pkl'))

def _iterate_run(combinations):
    """iterate over all the combinations and run the simulation"""
    all_results = {'cost': []}
    for i in combinations.index:
        info('\n' + '#' * 30 +
             '\nExploration iteration ' +
             '{}/{}\n'.format(i + 1,
                              len(combinations.index)) +
             '#' * 30 + '\n')
        _set_config(combinations.ix[i])
        new_results = _run_simulation()
        info(new_results)
        _process_results(all_results, new_results)
        results = pd.DataFrame(all_results)
        _serialise_results(combinations, results)
    return results

def explore():
    """explore different parameters"""
    combinations = _generate_combinations()
    results = _iterate_run(combinations)
