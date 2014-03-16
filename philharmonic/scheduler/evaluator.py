"""Evaluates a simulation, based on the cloud, environment and the actually
performed schedule of actions.

"""

import pandas as pd
import numpy as np

import philharmonic as ph

def print_history(cloud, environment, schedule):
    request_names = set(['boot', 'delete'])
    for t in environment.itertimes():
        requests = environment.get_requests()
        period = environment.get_period()
        actions = schedule.filter_current_actions(t, period)

        print('---t={}----'.format(t))
        if len(requests) > 0:
            print(" - requests:")
            print("    {}".format(str(requests.values)))
        # only take non-request actions (migrations)
        actions = [a for a in actions.values if a.name not in request_names]
        if len(actions) > 0:
            print(" - actions:")
            print("    {}".format(str(actions)))
            print('')

# TODO: add optional start, end limiters for evaluating a certain period

def calculate_cloud_utilisation(cloud, environment, schedule,
                                start=None, end=None):
    """Calculate utilisations of all servers based on the given schedule.

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    """
    if start is None:
        start = environment.start
        cloud.reset_to_initial() # TODO: timestamp states and be smarter
    else:
        cloud.reset_to_real()
    if end is None:
        end = environment.end
    #TODO: use more precise pandas methods for indexing (performance)
    #TODO: maybe move some of this state iteration functionality into Cloud
    #TODO: see where schedule window should be propagated - here or Scheduler?
    initial_utilisations = cloud.get_current().calculate_utilisations()
    utilisations_list = [initial_utilisations]
    times = [start]
    for t in schedule.actions.index.unique():
        if t == start: # we change the initial utilisation right away
            utilisations_list = []
            times = []
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                cloud.apply(action)
        else:
            action = schedule.actions[t]
            cloud.apply(action)
        state = cloud.get_current()
        new_utilisations = state.calculate_utilisations()
        utilisations_list.append(new_utilisations)
        times.append(t)
    if times[-1] < end:
        # the last utilisation values hold until the end - duplicate last
        times.append(end)
        utilisations_list.append(utilisations_list[-1])
    df_util = pd.DataFrame(utilisations_list, times)
    return df_util

def precreate_synth_power(start, end, servers):
    P_peak = 200
    P_idle = 100
    globals()['P_idle'] = P_idle
    P_delta = P_peak - P_idle
    power_freq = '5min'

    index = pd.date_range(start, end, freq=power_freq)
    P_synth_flat = pd.DataFrame({s: P_delta for s in servers}, index)
    globals()['P_synth_flat'] = P_synth_flat

#TODO: this function uses most of the simulation time
# - improve it
# - make sure it's called only when necessary
# - maybe pregenerate a power signal for the whole simulation and
#   slice it and scale it
# USE PRECREATED POWER
# TODO: get rid of this globals nonsense and create a Class (or a generator)
def generate_cloud_power(util, start=None, end=None):
    """Create power signals from varying utilisation rates."""
    P_std = 5 # 1.26 # P_delta * 0.05

    if start is None:
        start = util.index[0]
    if end is None:
        end = util.index[-1]

    P_synth_overlap = P_synth_flat[start:end]
    power = (P_synth_overlap * util).fillna(method='pad')
    P_idle = globals()['P_idle']
    # a server with no load is suspended
    power[power > 0] += P_idle + P_std * np.random.randn(len(power),
                                                         len(util.columns))
    return power

def calculate_cloud_cost(power, el_prices):
    """Take power and el. prices DataFrames & calc. the el. cost."""
    start = power.index[0]
    end= power.index[-1]
    el_prices_loc = pd.DataFrame()
    for server in power.columns: # this might be very inefficient
        loc = server.loc
        el_prices_loc[server] = el_prices[loc][start:end]
    cost = ph.calculate_price(power, el_prices_loc)
    return cost

def calculate_cloud_cooling(power, temperature):
    """Take power and temperature DataFrames & calculate the power with
    cooling overhead.

    """
    start = power.index[0]
    end= power.index[-1]
    temperature_server = pd.DataFrame()
    for server in power.columns: # this might be very inefficient
        loc = server.loc
        temperature_server[server] = temperature[loc][start:end]
    #cost = ph.calculate_price(power, el_prices_loc)
    power_with_cooling = ph.calculate_cooling_overhead(power,
                                                       temperature_server)
    return power_with_cooling

def _worst_case_power(cloud, environment, start, end): # TODO: use this
    """ the power if all the servers were fully utilised"""
    utilisations = {server : [1.0, 1.0] for server in cloud.servers}
    full_util = pd.DataFrame(utilisations,
                           index=[start, end])
    full_power = generate_cloud_power(full_util)

def combined_cost(cloud, environment, schedule, el_prices, temperature=None,
                  start=None, end=None):
    """calculate costs in one function"""

    # we first calculate utilisation with start, end = None / some timestamp
    # this way it knows which state to start from
    # (this is a temp. hack until cloud states get timestamped)
    util = calculate_cloud_utilisation(cloud, environment, schedule, start, end)
    if start is None:
        start = environment.start
    if end is None:
        end = environment.end
    power = generate_cloud_power(util)
    if temperature is not None:
        power = calculate_cloud_cooling(power, temperature[start:end])
    cost = calculate_cloud_cost(power, el_prices[start:end])
    total_cost = cost.sum() # for the whole cloud
    return total_cost

def normalised_combined_cost(cloud, environment, schedule,
                             el_prices, temperature=None, start=None, end=None):
    """Calculates combined costs and normalises them from 0. to 1.0 relative to
    a theoretical worst and best case.

    """
    if start is None:
        start = environment.start
    if end is None:
        end = environment.end

    actual_cost = combined_cost(cloud, environment, schedule,
                                el_prices, temperature, start, end)
    best_cost = 0.

    # worst case (full utilisation)
    utilisations = {server : [1.0, 1.0] for server in cloud.servers}
    full_util = pd.DataFrame(utilisations,
                             index=[start, end])
    full_power = generate_cloud_power(full_util)
    if temperature is not None:
        full_power = calculate_cloud_cooling(full_power, temperature[start:end])
    cost = calculate_cloud_cost(full_power, el_prices[start:end])
    worst_cost = cost.sum() # worst cost for the whole cloud

    # worst = 1.0, best = 0.0
    normalised = best_cost + actual_cost/worst_cost
    return normalised


#------------------------
# constraint_penalties
#------------------------

def calculate_constraint_penalties(cloud, environment, schedule,
                                   start=None, end=None):
    """Find all violated hard constraints for the given schedule
    and calculate appropriate penalties.

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    no constraints violated: 0.0

    the more constraintes valuated: closer to 1.0

    """
    cap_weight, sched_weight = 0.6, 0.5

    utilisations = {server : [] for server in cloud.servers}
    penalties = {}
    if start is None:
        start = environment.start
        cloud.reset_to_initial() # TODO: timestamp states and be smarter
    else:
        cloud.reset_to_real()
    if end is None:
        end = environment.end
    # if no actions - scheduling penalty for >0 VMs
    penalties[start] = sched_weight * np.sign(len(cloud.vms))
    for t in schedule.actions[start:end].index.unique():
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                cloud.apply(action)
        else:
            action = schedule.actions[t]
            cloud.apply(action)
        state = cloud.get_current()
        # find violated server capacity constraints TODO: find by how much
        cap_penalty = 1 - int(state.all_within_capacity())
        # find unscheduled VMs TODO: find how many are not allocated
        sched_penalty = 1 - int(state.all_allocated())
        penalty = cap_weight * cap_penalty + sched_weight * sched_penalty
        penalties[t] = penalty
    if len(schedule.actions) > 0:
        penalties[end] = penalty # last penalty holds 'til end

    penalties = pd.Series(penalties)
    constraint_penalty = ph.weighted_mean(penalties)
    return constraint_penalty

def calculate_sla_penalties(cloud, environment, schedule,
                            start=None, end=None):
    """1 migration per VM: 0.0; more migrations - closer to 1.0.

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    """
    # count migrations
    migrations_num = {vm: 0 for vm in cloud.vms}
    if start is None:
        start = environment.start
        cloud.reset_to_initial() # TODO: timestamp states and be smarter
    else:
        cloud.reset_to_real()
    if end is None:
        end = environment.end
    for t in schedule.actions[start:end].index.unique():
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                migrations_num[action.vm] += 1
        else:
            action = schedule.actions[t]
            migrations_num[action.vm] += 1
    migrations_num = pd.Series(migrations_num)
    if len(migrations_num) == 0:
        return 0. # no migrations - awesome!
    # average migration rate per hour
    duration = (end - start).total_seconds() / 3600
    migrations_rate = migrations_num / duration
    # Migration rate penalty - linear 1-4 migr/hour -> 0.0-1.0
    penalty =  (migrations_rate - 1) / 3.
    penalty[penalty<0] = 0
    penalty[penalty>1] = 1
    # 1/hour - tolerated, >1/hour - bad
    return penalty.mean()

# TODO: utilisation, constraint and sla penalties could all be
# calculated in one pass through the states

# TODO: add migration energy overhead into the energy calculation


#-------------------------------------
# simplified evaluator
#  - used for the GA fitness function
#-------------------------------------

# - one run from t to forecast_end
# - apply actions on the cloud model
#   - calculate utilisation
#   - count migration rate
#   - note capacity constraint violations
#
# - in the fitness function
#   - calculate simple measure of utilisation * el_price
#      - e.g. 
