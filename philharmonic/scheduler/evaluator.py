"""Evaluates a simulation, based on the cloud, environment and the actually
performed schedule of actions

"""

import pandas as pd
import numpy as np

def print_history(cloud, environment, schedule):
    for t in environment.itertimes():
        requests = environment.get_requests()
        period = environment.get_period()
        actions = schedule.filter_current_actions(t, period)

        print('---t={}----'.format(t))
        if len(requests) > 0:
            print(" - requests:")
            print("    {}".format(str(requests.values)))
        if len(actions) > 0:
            print(" - actions:")
            print("    {}".format(str(actions.values)))
            print('')

def calculate_cloud_utilisation(cloud, environment, schedule):
    """Calculate utilisations of all servers based on the given schedule"""
    cloud.reset_to_initial()
    #TODO: maybe move some of this state iteration functionality into Cloud
    states = []
    states.append(cloud.get_current())
    utilisations = {server : [0.0] for server in cloud.servers}
    for t, action in schedule.actions.iteritems():
        cloud.apply(action)
        state = cloud.get_current()
        states.append(state)
        new_utilisations = state.calculate_utilisations()
        for server, utilisation in new_utilisations.iteritems():
            utilisations[server].append(utilisation)
    # the last utilisation values hold until the end - duplicate last value
    for server, utilisation in new_utilisations.iteritems():
        utilisations[server].append(utilisation)

    # TODO: add end from environment
    times = [t for t in schedule.actions.keys()]
    times = [environment.start] + times + [environment.end]

    df_util = pd.DataFrame(utilisations, index=times)
    #df_all = df_util.join(schedule.actions)
    return df_util

def generate_cloud_power(util):
    """Create power signals from varying utilisation rates."""
    P_peak = 200
    P_idle = 100
    P_delta = P_peak - P_idle
    P_std = 1.26 # P_delta * 0.05
    power_freq = '5min'

    power = pd.DataFrame()
    for server in util.columns:
        start = util.index[0]
        end = util.index[-1]
        index = pd.date_range(start, end, freq=power_freq)
        synth_data = P_delta + P_std * np.random.randn(len(index))
        P_synth = pd.TimeSeries(data=synth_data, index=index)

        server_util = util[server]
        server_util = server_util.reindex(index, method='pad')

        power[server] = P_synth * server_util
    power[power>0] += P_idle # a server with no load is suspended
