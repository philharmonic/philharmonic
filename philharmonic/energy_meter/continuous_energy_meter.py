'''
Created on Jun 18, 2012

@author: kermit
'''

import threading
import time
from Queue import Empty
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import os
import pickle
from datetime import timedelta
import copy

from haley_api import Wattmeter
from philharmonic.energy_meter.exception import SilentWattmeterError

def log(message):
    print(message)
    logging.info(message)

class ContinuousEnergyMeter(threading.Thread):
    '''
    An energy meter that runs in the background (in a separate thread).
    '''


    def __init__(self, machines, metrics, interval, location="energy_data.pickle"):
        '''
        Constructor
        @param machines: list of hostnames of machines to monitor
        @param metrics: list of method objects that the energy meter will perform and get the results of   
        @param interval: number of seconds to wait between measurements
        @param location: where to store the time series pickle

        Builds an internal representation in self.data as a multi-index Dataframe, e.g.

        machine     metric                 14:24:24         14:24:25       ...
        ---------------------------------------------------------------------------
        snowwhite   active_power              38               39
                    apparent_power            57               55
        bashful     active_power              50               47
                    apparent_power            78               80
        ---------------------------------------------------------------------------
        '''
        threading.Thread.__init__(self)

        #self.q = q
        self.machines = machines
        self.metrics = metrics
        self.interval = interval
        self.location = location

        self.energy_meter =Wattmeter()

        #this is under haley_api now
        index_tuples = [(machine, metric) for machine in self.machines for metric in self.metrics]
        index = pd.MultiIndex.from_tuples(index_tuples, names=["machine", "metric"])
        self.data = pd.DataFrame({}, index = index)

        logging.basicConfig(filename='io/energy_meter.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        log("\n-------------\nENERGY_METER\n-------------")
        log("#wattmeter#start")

    def get_all_data(self):
        """
        @return: DataFrame containing measurements collected so far
        """
        return self.data

    def _add_current_data(self):
        """
        Fetch current measurements from the energy meter
        and add them to the past ones.
        """
#        new_values = []
#        for machine, metric in self.index_tuples:
#            new_values.append(self.energy_meter.measure_single(machine, metric))
#        new_series = pd.Series(new_values, index = self.index)
        try:
            new_series = self.energy_meter.measure_multiple(self.machines, self.metrics)
        except SilentWattmeterError:
            log("Wattmeter doesn't respond too long. Quitting.")
            self._finalize()
            raise
        current_time = datetime.now()
        self.data[current_time] = new_series

    def _finalize(self): 
        self.data.to_pickle(self.location)
        log("#wattmeter#end")
        log("-------------\n")

    def run(self):
        while True:
            self._add_current_data()
            time.sleep(self.interval)
            try:
                message = self.q.get_nowait()
                if message == 'quit':
                    self._finalize()
                    break
                else:
                    self.q.put(message)
            except Empty:
                pass
        print("Stopping background measurements.")

class Measurement():
    pass

def  deserialize_folder(base_loc):
    """read the pd.DataFrame pickled by the ContinuousEnergyMeter"""
    # find the location
    m = Measurement()
    base_loc = os.path.expanduser(base_loc)
    # Load the benchmark results
    with open(os.path.join(base_loc, "results.pickle")) as results_pickle:
        #print(hashlib.md5(results_pickle.read()).hexdigest())
        results_pickle.seek(0)
        results = pickle.load(results_pickle)
        m.start = results["start"]
        m.end = results["end"]
        m.duration = results["duration"]
    # Load the energy measurements
    energy_data = pd.read_pickle(os.path.join(base_loc, "energy_consumption.pickle"))
    # Cut off only the energy measurements during the benchmark.
    buffer = timedelta(minutes=2)
    # columns and rows kinda upside-down, so tranpose
    m.energy_data = energy_data.transpose()[m.start-buffer:m.end+buffer]
    return m

def synthetic_power(mean, std, start, end, freq='5s'):
    """build an artificial power time series"""
    index = pd.date_range(start, end, freq='5s', name='Time')
    P_synth = pd.Series(np.random.normal(mean, std, len(index)), index, name='Power')
    P_synth.ix[P_synth < 0] = 0
    return P_synth

def build_synth_measurement(m, P_peak, en_elasticity=0.5, ewma_span=100):
    """build an artificial copy of a Measurement with arbitrary
    peak and idle power values.

    """
    std_peak = m.active_power[m.active_power>40].std()
    P_synth_peak = synthetic_power(P_peak, std_peak, '2012-11-01', '2012-11-10')

    P_idle = P_peak * en_elasticity
    std_idle = m.active_power[m.active_power<40].std()
    P_synth_idle = synthetic_power(P_idle, std_idle, '2012-11-01', '2012-11-10')

    start = m.active_power.index[0]
    end = m.active_power.index[-1]
    pause_start = m.active_power[m.active_power<40].index[0]
    pause_end = m.active_power[m.active_power<40].index[-1]
    m_synth = copy.deepcopy(m)
    m_synth.active_power = pd.concat([P_synth_peak[start:pause_start],
                                      P_synth_idle[pause_start:pause_end],
                                      P_synth_peak[pause_end:end]])
    m_synth.ewma_power = pd.ewma(m_synth.active_power, span=ewma_span)

    return m_synth
