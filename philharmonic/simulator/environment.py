import pandas as pd

import inputgen

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
    def __init__(self, *args):
        super(SimulatedEnvironment, self).__init__()
        self._t = None

    def set_time(self, t):
        self._t = t

    def get_time(self):
        return self._t

    t = property(get_time, set_time, doc="current time")

    def set_period(self, period):
        self._period = period

    def get_period(self):
        return self._period

    period = property(get_period, set_period, doc="period between time steps")

class PPSimulatedEnvironment(SimulatedEnvironment):
    """Peak pauser simulation scenario with one location, el price"""
    pass

class FBFSimpleSimulatedEnvironment(SimulatedEnvironment):
    """Couple of requests in a day."""
    def __init__(self, times=None, requests=None):
        """@param times: list of time ticks"""
        super(SimulatedEnvironment, self).__init__()
        if not times is None:
            self._times = times
            self._period = times[1] - times[0]
            self.start = self._times[0]
            self.end = self._times[-1]
            if requests is not None:
                self._requests = requests
            else:
                self._requests = inputgen.normal_vmreqs(self.start, self.end)

    def itertimes(self):
        """Generator that iterates over times. To be called by the simulator."""
        for t in self._times:
            self._t = t
            yield t

    def itertimes_immutable(self):
        """Like itertimes, but doesn't alter state. Goes from start to end."""
        t = self.start
        while t <= self.end:
            yield t
            t += self._period

    def times_index(self):
        """Return a pandas Index based on the set times"""
        idx = pd.date_range(start=self.start, end=self.end, freq=self.period)
        return idx

    def get_requests(self):
        start = self.get_time()
        justabit = pd.offsets.Micro(1)
        end = start + self._period - justabit
        return self._requests[start:end]
