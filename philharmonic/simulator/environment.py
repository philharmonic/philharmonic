class Environment(object):
    """provides data about all the data centers
    - e.g. the temperature and prices at different location

    """
    def __init__(self):
        pass

    def current_data(self):
        """return all the current data for all the locations"""
        raise NotImplemented

class SimulatedEnvironment(Environment):
    """stores and provides simulated data about the environment
    - e.g. the temperature and prices at different location

    """
    def __init__(self):
        super(SimulatedEnvironment, self).__init__()
        self._t = None

    def set_time(self, t):
        self._t = t

    def get_time(self):
        return self._t

    def get_period(self):
        return self.period

    t = property(get_time, set_time, doc="current time")

class PPSimulatedEnvironment(SimulatedEnvironment):
    """Peak pauser simulation scenario with one location, el price"""
    pass

class FBFSimpleSimulatedEnvironment(SimulatedEnvironment):
    """Couple of requests in a day."""
    def __init__(self, times):
        """@param times: list of time ticks"""
        super(SimulatedEnvironment, self).__init__()
        self._times = times

    def itertimes(self):
        """Generator that iterates over times. To be called by the simulator."""
        for t in self._times:
            self._t = t
            yield t
