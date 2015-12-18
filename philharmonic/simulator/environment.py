import pandas as pd
import numpy as np

import inputgen

def cleaned_requests(requests):
    """return requests with simultaneous boot & delete actions removed"""
    times = []
    values = []
    del_vms = set([req.vm for req in requests.values if req.what == 'delete'])
    boot_vms = set([req.vm for req in requests.values if req.what == 'boot'])
    useless_vms = boot_vms.intersection(del_vms)
    for t, req in requests.iteritems():
        if req.vm not in useless_vms:
            values.append(req)
            times.append(t)
    return pd.Series(values, times)
    return requests

class Environment(object):
    """provides data about all the data centers
    - e.g. the temperature and prices at different location

    """
    def __init__(self):
        pass

    def __repr__(self):
        return repr({'start': self.start, 'end': self.end,
                     'period': self.period,
                     '_forecast_periods': self._forecast_periods})

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

    def set_forecast_periods(self, num_periods):
        self._forecast_periods = num_periods

    def get_forecast_periods(self, num_periods):
        return self._forecast_periods

    forecast_periods = property(get_forecast_periods, set_forecast_periods,
                                doc="number of periods we get forecasts for")

    def get_forecast_end(self): # TODO: parametrize
        return self._t + self._forecast_periods * self._period

    forecast_end = property(get_forecast_end, doc="time by which we forecast")

    def current_data(self, forecast=True):
        """Return el. prices and temperatures from now to forecast_end with
        optional forecasting error (for forecast=True).

        """
        if forecast and hasattr(self, 'forecast_el'):
            el_prices = self.forecast_el[self.t:self.forecast_end]
        else:
            el_prices = self.el_prices[self.t:self.forecast_end]

        if self.temperature is not None:
            if forecast and hasattr(self, 'forecast_temp'):
                temperature = self.forecast_temp[self.t:self.forecast_end]
            else:
                temperature = self.temperature[self.t:self.forecast_end]
        return el_prices, temperature

    def _generate_forecast(self, data, SD):
        return data + SD * np.random.randn(*data.shape)

    def model_forecast_errors(self, SD_el, SD_temp):
        self.forecast_el = self._generate_forecast(self.el_prices, SD_el)
        if not self.temperature is None:
            self.forecast_temp = self._generate_forecast(self.temperature, SD_temp)

class PPSimulatedEnvironment(SimulatedEnvironment):
    """Peak pauser simulation scenario with one location, el price"""
    pass

# TODO: merge these two with SimulatedEnvironment
class FBFSimpleSimulatedEnvironment(SimulatedEnvironment):
    """Couple of requests in a day."""
    def __init__(self, times=None, requests=None, forecast_periods=24):
        """@param times: list of time ticks"""
        super(SimulatedEnvironment, self).__init__()
        if not times is None:
            self._times = times
            self._period = times[1] - times[0]
            #self._period = pd. # TODO: switch to above when issue with pandas fixed
            self._t = self._times[0]
            self.start = self._times[0]
            self.end = self._times[-1]
            if requests is not None:
                self._requests = requests
            else:
                self._requests = inputgen.normal_vmreqs(self.start, self.end)
        else:
            self._t = 0
            self._period = 1
            self.el_prices = []
            self.temperature = []
        self._forecast_periods = forecast_periods

    # TODO: better to make the environment immutable
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
        # TODO: figure out how to turn self.period into a DateOffset
        return idx

    def forecast_window_index(self):
        """Return a pandas Index from t to forecast_end"""
        #idx = pd.date_range(start=self.t, end=self.forecast_end,
        #                    freq=self.period)
        idx = self.times_index()[self.t, self.forecast_end]
        return idx

    def get_requests(self):
        start = self.get_time()
        justabit = pd.offsets.Micro(1)
        end = start + self._period - justabit
        #TODO: if same vm booted & deleted at once, skip it
        return cleaned_requests(self._requests[start:end])

class GASimpleSimulatedEnvironment(FBFSimpleSimulatedEnvironment):
    pass
