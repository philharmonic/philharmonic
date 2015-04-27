"""Evaluates a simulation, based on the cloud, environment and the actually
performed schedule of actions.

"""

import math

import pandas as pd
import numpy as np

import philharmonic as ph
from philharmonic.logger import *
from philharmonic import conf

def print_history(cloud, environment, schedule):
    """Print the schedule in a human-readable format."""
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
    # P_peak = conf.P_peak
    # P_idle = conf.P_idle
    # globals()['P_idle'] = P_idle
    # P_delta = P_peak - P_idle
    # power_freq = conf.power_freq

    # index = pd.date_range(start, end, freq=power_freq)
    # P_synth_flat = pd.DataFrame({s: P_delta for s in servers}, index)
    # globals()['P_synth_flat'] = P_synth_flat

    full_util = {server : [1.0, 1.0] for server in servers}
    full_util = pd.DataFrame(full_util,
                             index=[start, end])
    full_util = full_util.resample('H', fill_method='pad')
    globals()['full_util'] = full_util

    globals()['cached_end'] = None

# TODO: get rid of this globals nonsense and create a Class (or a generator)
def generate_cloud_power(util, start=None, end=None,
                         power_freq_model=None, freq=None):
    """Create power signals from varying utilisation rates."""
    if power_freq_model is None:
        power_freq_model = conf.power_freq_model
    if freq is None:
        freq = 2000
    # calculate on a sparse util DataFrame
    if power_freq_model:
        #TODO: get frequencies from the servers
        power = ph.calculate_power_freq(
            util, f=freq, P_idle=conf.P_idle, P_base=conf.P_base,
            P_dif=conf.P_dif, f_base=conf.f_base
        )
    else:
        power = ph.calculate_power(util, conf.P_idle, conf.P_peak)
    # fill it out to the full frequency
    power = power.resample(conf.power_freq, fill_method='pad')
    # add random noise
    power[power > 0] += conf.P_std * np.random.randn(*power.shape)
    return power

def calculate_cloud_cost(power, el_prices):
    """Take power and el. prices DataFrames & calc. the el. cost."""
    start = power.index[0]
    end= power.index[-1]
    el_prices_loc = pd.DataFrame()
    for server in power.columns: # this might be very inefficient
        loc = server.loc
        el_prices_loc[server] = el_prices[loc][start:end]
    cost = ph.calculate_price(power, el_prices_loc)#ph.calculate_price_mean(power, el_prices_loc)
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

def _get_freq_or_none(cloud, environment, schedule, start, end):

    return freq

def _worst_case_power(cloud, environment, start, end): # TODO: use this
    """The power if all the servers were fully utilised."""
    utilisations = {server : [1.0, 1.0] for server in cloud.servers}
    full_util = pd.DataFrame(utilisations,
                           index=[start, end])
    if conf.power_freq_model:
        full_freq = {server : [1.0, 1.0] for server in cloud.servers}
        full_freq = pd.DataFrame(full_freq,
                                 index=[start, end])
        full_freq = full_freq * conf.f_max
    else:
        full_freq = None
    full_power = generate_cloud_power(full_util, freq=full_freq)

def combined_cost(cloud, environment, schedule, el_prices, temperature=None,
                  start=None, end=None):
    """Calculate energy costs including IT equipment energy cooling overhead and
    the real-time electricity price."""

    # we first calculate utilisation/freq with start, end = None / timestamp
    # this way it knows which state to start from
    # (this is a temp. hack until cloud states get timestamped)
    util = calculate_cloud_utilisation(cloud, environment, schedule, start, end)
    if conf.power_freq_model:
        freq = calculate_cloud_frequencies(
            cloud, environment, schedule, start, end
        )
    else:
        freq = None
    power = generate_cloud_power(util, freq=freq)
    if start is None:
        start = environment.start
    if end is None:
        end = environment.end
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

def combined_energy(cloud, environment, schedule, temperature=None,
                    start=None, end=None):
    """Calculate energy of IT equipment and cooling if temperature provided.

    @returns: energy in kWh

    """

    # we first calculate utilisation with start, end = None / some timestamp
    # this way it knows which state to start from
    # (this is a temp. hack until cloud states get timestamped)
    util = calculate_cloud_utilisation(cloud, environment, schedule, start, end)
    if start is None:
        start = environment.start
    if end is None:
        end = environment.end
    if conf.power_freq_model:
        freq = calculate_cloud_frequencies(cloud, environment, schedule,
                                           start, end)
    else:
        freq = None
    power = generate_cloud_power(util, freq=freq)
    if temperature is not None:
        power = calculate_cloud_cooling(power, temperature[start:end])
    energy = ph.calculate_energy(power)
    energy_total = energy.sum() # for the whole cloud
    energy_total = ph.joul2kwh(energy_total)
    return energy_total

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
    cap_weight, sched_weight = 0.6, 0.4

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
        # find violated server capacity constraints - how many violations
        cap_penalty = 1 - state.ratio_within_capacity()
        # find unscheduled VMs - how many are not allocated
        sched_penalty = 1 - state.ratio_allocated()
        penalty = cap_weight * cap_penalty + sched_weight * sched_penalty
        penalties[t] = penalty
    if len(schedule.actions) > 0:
        penalties[end] = penalty # last penalty holds 'til end

    penalties = pd.Series(penalties)
    constraint_penalty = ph.weighted_mean(penalties)
    return constraint_penalty

def calculate_sla_penalties(cloud, environment, schedule,
                            start=None, end=None):
    """One migration per VM: 0.0; more migrations - closer to 1.0.

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

alpha = 0.512
beta = 20.165
E_mig = lambda V_mig : alpha*V_mig + beta
V_mig = lambda V_mem, R, D, n : V_mem * (1-(D/float(R))**(n+1))/(1-D/float(R))
T_mig = lambda V_mig, R : V_mig/(R/8.) # R assumed to be in Mb/s
# constants
R, D = 1000, 300
V_thd = 100 # MB; treshold after which post-copying starts

def calculate_migration_overhead(cloud, environment, schedule,
                                 start=None, end=None):
    """For every migration, calculate the energy using the  Liu et al. model,
    take the mean electricity price between the current and target locations,
    and calculate the resulting cost.

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    @returns: energy in kWh, cost in $

    """
    if start is None:
        start = environment.start
        cloud.reset_to_initial() # TODO: timestamp states and be smarter
    else:
        cloud.reset_to_real()
    if end is None:
        end = environment.end

    total_energy = 0.
    total_cost = 0.
    for t in schedule.actions[start:end].index.unique():
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            actions = [action for action in schedule.actions[t].values]
        else:
            actions = [schedule.actions[t]]
        for action in actions:
            if action.name not in set(['boot', 'delete', 'migrate']):
                continue # we're not interested in other actions
            before = cloud.get_current()
            host_before = before.allocation(action.vm)
            cloud.apply(action)
            after = cloud.get_current()
            host_after = after.allocation(action.vm)
            #if host_before or host_after is None, it's a boot/delete
            if (action.name == 'migrate' and host_before and
                host_after and host_before != host_after):
                price_before = environment.el_prices[host_before.loc][t]
                price_after = environment.el_prices[host_after.loc][t]
                mean_el_price = (price_before + price_after) / 2.

                memory = action.vm.res['RAM'] * 1000 # MB
                try:
                    n = int(math.ceil(math.log(V_thd/float(memory),
                                               D/float(R))))
                except ZeroDivisionError:
                    n = 1 # TODO: check what raises this error
                migration_data = V_mig(memory, R, D, n)
                energy = E_mig(migration_data) # Joules
                energy = ph.joul2kwh(energy) # kWh
                total_energy += energy
                cost = energy * mean_el_price
                total_cost += cost
    return total_energy, total_cost

# TODO: utilisation, constraint and sla penalties could all be
# calculated in one pass through the states

# TODO: add migration energy overhead into the energy calculation


#-------------------------------------
# simplified evaluator
#  - used for the GA fitness function
#-------------------------------------

# - one run from t to forecast_end
# - apply actions on the cloud model (inplace for speed)
#   - calculate utilisation
#   - count migration rate
#   - note capacity constraint violations
#
# - in the fitness function
#   - calculate simple measure of utilisation * el_price
#      - e.g. utilprice = tot_util * el_price

def _calculate_constraint_penalty(state):
    # find violated server capacity constraints - how many violations
    cap_penalty = state.capacity_penalty()
    # find unscheduled VMs - how many are not allocated
    sched_penalty = 1 - state.ratio_allocated()
    return cap_penalty, sched_penalty

def _reset_cloud_state(cloud, environment, start=None, end=None):
    """Undo any actions applied after the _real (if start given)
    or _initial state (if start is None).

    """
    if start is None:
        start = environment.start
        cloud.reset_to_initial() # TODO: timestamp states and be smarter
    else:
        cloud.reset_to_real()
    if end is None:
        end = environment.end
    return start, end

def evaluate(cloud, environment, schedule,
             el_prices, temperature=None,
             start=None, end=None):
    """Calculate utilprice, sla and contstraint penalties
    of all servers based on the given schedule.

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    """
    start, end = _reset_cloud_state(cloud, environment, start, end)
    #TODO: use more precise pandas methods for indexing (performance)
    #TODO: maybe move some of this state iteration functionality into Cloud
    #TODO: see where schedule window should be propagated - here or Scheduler?
    initial_utilisations = cloud.get_current().calculate_utilisations()
    utilisations_list = [initial_utilisations]
    times = [start]

    # CONSTRAINTS
    cap_weight, sched_weight = 0.6, 0.4
    penalties = {}
    # if no actions - penalty for the current state
    # or penalty for start -> t
    cap_penalty, sched_penalty = _calculate_constraint_penalty(
        cloud.get_current())
    penalty = cap_weight * cap_penalty + sched_weight * sched_penalty
    penalties[start] = penalty

    # SLA
    migrations_num = {vm: 0 for vm in cloud.vms}

    for t in schedule.actions.index.unique():
        if t == start: # we change the initial utilisation right away
            utilisations_list = []
            times = []
            # we remove the initial penalty, as there are immediate actions
            penalties = {}
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                cloud.apply(action, inplace=True)
                try:
                    migrations_num[action.vm] += 1
                except KeyError:
                    error('Explosion! Check environment.get_requests.')
                    raise
        else:
            action = schedule.actions[t]
            try:
                migrations_num[action.vm] += 1
            except KeyError:
                error('Explosion! Check environment.get_requests.')
                raise
            cloud.apply(action, inplace=True)
        state = cloud.get_current()
        new_utilisations = state.calculate_utilisations()
        utilisations_list.append(new_utilisations)
        times.append(t)

        # CONSTRAINTS
        cap_penalty, sched_penalty = _calculate_constraint_penalty(state)
        penalty = cap_weight * cap_penalty + sched_weight * sched_penalty
        penalties[t] = penalty

    if times[-1] < end:
        # the last utilisation values hold until the end - duplicate last
        times.append(end)
        utilisations_list.append(utilisations_list[-1])

    util = pd.DataFrame(utilisations_list, times)

    # CONSTRAINTS
    #if len(schedule.actions) > 0: # <- not sure why this if was necessary
    penalties[end] = penalty # last penalty holds 'til end
    # CONSTRAINTS
    penalties = pd.Series(penalties)
    constraint_penalty = ph.weighted_mean(penalties)

    # SLA
    migrations_num = pd.Series(migrations_num)
    if len(migrations_num) == 0:
        sla_penalty = 0. # no migrations - awesome!
    else:
        # average migration rate per 4 hours
        duration = (end - start).total_seconds() / 3600 # hours
        migrations_rate = 4 * migrations_num / duration
        # Migration rate penalty - linear 1-4 migr/4 hours -> 0.0-1.0
        penalty =  (migrations_rate - 1) / 3.
        penalty[penalty<0] = 0
        penalty[penalty>1] = 1
        # 1 / 4 hours - tolerated, >1 / 4 hours - bad
        sla_penalty = penalty.mean()

    # COST GOAL
    #----------
    # utility + cooling + el. price penalty
    # -load some cached data (or create & cache if it's a miss)
    if globals()['cached_end'] == end:
        el_prices_server = globals()['el_prices_server']
        utilprice_worst_avg = globals()['utilprice_worst_avg']
        el_prices_current = globals()['el_prices_current']
    else:
        el_prices_current = el_prices[start:end]
        if temperature is not None:
            pPUE = ph.calculate_pue(temperature[start:end])
            el_prices_current = el_prices_current * pPUE
        globals()['el_prices_current'] = el_prices_current
        el_prices_server = pd.DataFrame()
        # TODO: multiply with pPUE - from the temperature model
        for server in util.columns: # this might be very inefficient
            loc = server.loc
            el_prices_server[server] = el_prices_current[loc]
        globals()['el_prices_server'] = el_prices_server
        globals()['cached_end'] = end

        # - worst case util
        full_util_current = globals()['full_util'][start:end]
        utilprice_worst = el_prices_server * full_util_current
        utilprice_worst_avg = utilprice_worst.mean().mean()
        globals()['utilprice_worst_avg'] = utilprice_worst_avg

    # -based on this utility
    util = util.reindex(el_prices_current.index, method='pad')
    utilprice = el_prices_server * util
    utilprice_avg = utilprice.mean().mean()
    utilprice_penalty = utilprice_avg / float(utilprice_worst_avg)

    # mean nonzero utilisation
    nonzero_utilisation_avg = util[util>0].mean().mean()
    if np.isnan(nonzero_utilisation_avg):
        nonzero_utilisation_avg = 0
    # goal: high utilisation -> 0.0 good, high utilisation; 1.0 low utilisation
    util_penalty = float(1 - nonzero_utilisation_avg)

    #cost_penalty = 0.2 * util_penalty + 0.8 * utilprice_penalty

    _reset_cloud_state(cloud, environment, start, end)

    return util_penalty, utilprice_penalty, constraint_penalty, sla_penalty

# TODO: maybe move to State.freq_scale_vms
def _server_freqs_to_vm_freqs(state):
    """Return a dict with VMs as keys and showing frequencies
    of servers hosting them in @param state.

    """
    vm_freq = {vm : state.freq_scale[state.allocation(vm)] for vm in state.vms}
    return vm_freq

def _get_frequencies(state, for_vms=False):
    """Get frequencies for VMs/servers in the given state as needed"""
    if for_vms:
        try:
            freq = _server_freqs_to_vm_freqs(state)
        except KeyError: # when VMs are not allocated anywhere
            freq = {}
    else:
        freq = state.freq_scale
    return freq

def calculate_cloud_frequencies(cloud, environment, schedule,
                                start=None, end=None, for_vms=False):
    """Calculate frequencies of all servers or VMs based on the given schedule.

    @param for_vms: if True return freqs for VMs, otherwise for servers

    @param start, end: if given, only this period will be counted,
    cloud model starts from _real. If not, whole environment.start-end
    counted and the first state is _initial.

    """
    start, end = _reset_cloud_state(cloud, environment, start, end)
    initial_freq = _get_frequencies(cloud.get_current(), for_vms)
    freq_list = [initial_freq]
    times = [start]
    for t in schedule.actions.index.unique():
        if t == start: # we change the initial frequencies right away
            freq_list = []
            times = []
        # TODO: precise indexing, not dict
        if isinstance(schedule.actions[t], pd.Series):
            for action in schedule.actions[t].values:
                cloud.apply(action)
        else:
            action = schedule.actions[t]
            cloud.apply(action)
        state = cloud.get_current()
        new_freq = _get_frequencies(state, for_vms)
        freq_list.append(new_freq)
        times.append(t)
    if times[-1] < end:
        # the last frequency values hold until the end - duplicate last
        times.append(end)
        freq_list.append(freq_list[-1])
    df_freq = pd.DataFrame(freq_list, times)
    # convert freq_scale to absolute value in Hz
    df_freq_hz = conf.f_max * df_freq
    return df_freq_hz

def calculate_service_profit(cloud, environment, schedule,
                             start=None, end=None):
    """Calculate the profit for the cloud provider for hosting the VMs."""

    if conf.power_freq_model:
        freq = calculate_cloud_frequencies(cloud, environment, schedule,
                                           start, end, for_vms=True)
    else:
        freq = None
    whole_timeline = (start is None) # called for whole simulation timeline
    start, end = _reset_cloud_state(cloud, environment, start, end)
    # TODO: test both cases
    if whole_timeline:
        considered_vms = set(environment._requests.apply(lambda a : a.vm))
    else:
        considered_vms = cloud.get_current().vms

    df_beta = pd.DataFrame(
        [{vm : vm.beta for vm in considered_vms}], [start]
    )
    if conf.power_freq_model:
        df_beta = df_beta.reindex(freq.index, method='pad')
    ram_size_base = 1 # 1000 # 1024
    ram_index = 'RAM'
    df_rel_ram = pd.DataFrame([{vm : vm.res[ram_index] / ram_size_base \
                                for vm in considered_vms}], [start])
    if conf.power_freq_model:
        df_rel_ram = df_rel_ram.reindex(freq.index, method='pad')
    # df_price = ph.vm_price_progressive(
    #     freq, df_beta, C_base=conf.C_base, C_dif=conf.C_dif_cpu,
    #     f_base=conf.f_base, f_max=conf.f_max
    # )
    if not conf.power_freq_model:
        freq = 0
    df_price = ph.vm_price_cpu_ram(
        df_rel_ram, freq, df_beta, C_base=conf.C_base, C_dif_cpu=conf.C_dif_cpu,
        C_dif_ram=conf.C_dif_ram, f_base=conf.f_base, f_max=conf.f_max
    )
    df_price = df_price.resample(conf.pricing_freq, fill_method='pad')
    total_profit = df_price.sum().sum()
    return total_profit

# TODO: move all the functions as methods in here, make global caches attributes
# and have it automatically recognise when geotemp. inputs have changed to
# cache the new results.
class Evaluator(object):
    pass
