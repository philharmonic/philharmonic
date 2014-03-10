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
    """Calculate utilisations of all servers based on the given schedule."""
    cloud.reset_to_initial()
    #TODO: maybe move some of this state iteration functionality into Cloud
    #TODO: see where schedule window should be propagated - here or Scheduler?
    utilisations = {server : [] for server in cloud.servers}
    times = []
    for t in schedule.actions.index.unique():
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                cloud.apply(action)
        else:
            action = schedule.actions[t]
            cloud.apply(action)
        state = cloud.get_current()
        #import ipdb; ipdb.set_trace()
        new_utilisations = state.calculate_utilisations()
        times.append(t)
        for server, utilisation in new_utilisations.iteritems():
            utilisations[server].append(utilisation)

    if start is None:
        start = environment.start
    if end is None:
        end = environment.end
    #TODO: use pandas methods
    try:
        if times[0] != start:
            times = [start] + times
            for server in cloud.servers:
                utilisations[server] = [0.0] + utilisations[server]

        if times[-1] != end:
            # the last utilisation values hold until the end - duplicate last
            times = times + [end]
            for server, utilisation in new_utilisations.iteritems():
                utilisations[server].append(utilisation)
    except IndexError: # no actions
        times = [start, end]
        for server in cloud.servers:
            utilisations[server] = [0.0, 0.0]

    df_util = pd.DataFrame(utilisations, index=times)
    #df_all = df_util.join(schedule.actions)
    return df_util

#TODO: this function uses most of the simulation time
# - improve it
# - make sure it's called only when necessary
# - maybe pregenerate a power signal for the whole simulation and
#   slice it and scale it
def generate_cloud_power(util, start=None, end=None):
    """Create power signals from varying utilisation rates."""
    P_peak = 200
    P_idle = 100
    P_delta = P_peak - P_idle
    P_std = 1.26 # P_delta * 0.05
    power_freq = '5min'

    if start is None:
        start = util.index[0]
    if end is None:
        end = util.index[-1]

    power = pd.DataFrame()
    index = pd.date_range(start, end, freq=power_freq)
    # reindex especially slow - scaling existing signal better
    server_util = util.reindex(index, method='pad')
    synth_data = P_delta + P_std * np.random.randn(len(index),
                                                   len(util.columns))
    P_synth = pd.DataFrame(synth_data, index=index, columns=util.columns)
    power = P_synth * server_util
    power[power>0] += P_idle # a server with no load is suspended
    return power

def calculate_cloud_cost(power, el_prices):
    """Take power and el. prices DataFrames & calc. the el. cost."""
    el_prices_loc = pd.DataFrame()
    for server in power.columns: # this might be very inefficient
        loc = server.loc
        el_prices_loc[server] = el_prices[loc]
    cost = ph.calculate_price(power, el_prices_loc)
    return cost

def calculate_cloud_cooling(power, temperature):
    """Take power and temperature DataFrames & calculate the power with
    cooling overhead.

    """
    temperature_server = pd.DataFrame()
    for server in power.columns: # this might be very inefficient
        loc = server.loc
        temperature_server[server] = temperature[loc]
    #cost = ph.calculate_price(power, el_prices_loc)
    power_with_cooling = ph.calculate_cooling_overhead(power,
                                                       temperature_server)
    return power_with_cooling

def combined_cost(cloud, environment, schedule, el_prices, temperature=None):
    """calculate costs in one method"""
    util = calculate_cloud_utilisation(cloud, environment, schedule)
    power = generate_cloud_power(util)
    if temperature is not None:
        power = calculate_cloud_cooling(power, temperature)
    cost = calculate_cloud_cost(power, el_prices)
    total_cost = cost.sum() # for the whole cloud
    return total_cost

def normalised_combined_cost(cloud, environment, schedule,
                             el_prices, temperature=None):
    """calculates combined costs and normalises them from 0. to 1.0 relative to
    a theoretical worst and best case.

    """
    actual_cost = combined_cost(cloud, environment, schedule,
                         el_prices, temperature=None)
    best_cost = 0.

    # worst cost (full utilisation)
    utilisations = {server : [1.0, 1.0] for server in cloud.servers}
    full_util = pd.DataFrame(utilisations,
                           index=[environment.start, environment.end])
    power = generate_cloud_power(full_util)
    if temperature is not None:
        power = calculate_cloud_cooling(power, temperature)
    cost = calculate_cloud_cost(power, el_prices)
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

    no constraints violated: 0.0

    the more constraintes valuated: closer to 1.0

    """
    cap_weight, sched_weight = 0.6, 0.5

    cloud.reset_to_initial()
    utilisations = {server : [] for server in cloud.servers}
    penalties = {}
    if not start:
        start = environment.start
    if not end:
        end = environment.end
    # if no actions - scheduling penalty for >0 VMs
    penalties[start] = sched_weight * np.sign(len(cloud.vms))
    for t in schedule.actions.index.unique():
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

def inc_migrations(migrations_num, vm):
    try:
        migrations_num[vm] += 1
    except KeyError:
        migrations_num[vm] = 1

def migr_rate_penalty(migr_rate):
    """Migration rate penalty - linear 1-4 migr/hour -> 0.0-1.0"""
    migr_rate

def calculate_sla_penalties(cloud, environment, schedule,
                            start=None, end=None):
    """1 migration per VM: 0.0; more migrations - closer to 1.0"""
    # count migrations
    cloud.reset_to_initial() # TODO: rethink this
    migrations_num = {}
    if not start:
        start = environment.start
    if not end:
        end = environment.end
    for t in schedule.actions.index.unique():
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                inc_migrations(migrations_num, action.vm)
        else:
            action = schedule.actions[t]
            inc_migrations(migrations_num, action.vm)
    migrations_num = pd.Series(migrations_num)
    # average migration rate per hour
    duration = (environment.end - environment.start).total_seconds() / 3600
    migrations_rate = migrations_num / duration
    penalty =  (migrations_rate - 1) / 3.
    penalty[penalty<0] = 0
    penalty[penalty>1] = 1
    # 1/hour - tolerated, >1/hour - bad
    return penalty.mean()

# TODO: utilisation, constraint and sla penalties could all be
# calculated in one pass through the states

# TODO: add migration energy overhead into the energy calculation
