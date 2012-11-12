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
        self.data.save(self.location)
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
        