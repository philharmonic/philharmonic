"""Evaluates a simulation, based on the cloud, environment and the actually
performed schedule of actions

"""

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

#TODO: check why some requests/actions filtered under the wrong timeslot
