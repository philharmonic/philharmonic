'''
Created on Oct 9, 2012

@author: kermit
'''

import time
from Queue import Queue, Empty
import logging
from datetime import datetime
import pickle

from philharmonic import conf
from energy_predictor import EnergyPredictor
import philharmonic.openstack.console_api as openstack
from philharmonic.scheduler.ischeduler import IScheduler

def log(message):
    print(message)
    logging.info(message)

class PeakPauser(IScheduler):
    def __init__(self):
        IScheduler.__init__(self)
        self.paused=False
        openstack.dummy = conf.dummy
        openstack.authenticate()
        

    def parse_prices(self, location, percentage_to_pause):
        self.energy_price = EnergyPredictor(location, percentage_to_pause)
    
    def price_is_expensive(self):
        return self.energy_price.is_expensive()
    
    def benchmark_done(self):
        try:
            self.results = self.q.get_nowait()
            return True  # benchmark done, we got the results 
        except Empty:  # benchmark still executing
            return False
        
    def pause(self):
        if not self.paused:
            if not conf.dummy:
                openstack.pause(conf.instance)
            self.paused = True
            log("paused")
    
    def unpause(self):
        if self.paused:
            if not conf.dummy:
                openstack.unpause(conf.instance)
            log("unpaused")
            self.paused = False
    
    def initialize(self):
        logging.basicConfig(filename='io/philharmonic.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        log("\n-------------\nPHILHARMONIC\n-------------")
        self.unpause()  # in case the VM was paused before we started
        self.parse_prices(conf.historical_en_prices, conf.percentage_to_pause)
        self.start = datetime.now()
        time.sleep(5) # give ourselves time to start the benchmark
        log("#scheduler#start %s" % str(self.start))
    
    def finalize(self):
        self.end = datetime.now()
        log("#scheduler#end %s" % str(self.end))
        self.duration = self.end - self.start
        log("#scheduler#runtime %s" % str(self.duration))
        self.unpause()  # don't leave a VM hanging after the experiment's done
        self.results = {"start":self.start, "end":self.end, "duration":self.duration}
        with open(conf.results, "wb") as results_file:
            pickle.dump(self.results, results_file)
        log("------------------\n")
        
    def run(self):
        self.initialize()
        while True:
            if self.benchmark_done():
                print("benchmark done")
                break
            if self.price_is_expensive():
                self.pause()
            else:
                self.unpause()
            time.sleep(conf.sleep_interval)
        self.finalize()

class NoScheduler(PeakPauser):
    
    def __init__(self):
        # call IScheduler's constructor
        super(PeakPauser, self).__init__()
    def initialize(self):
        logging.basicConfig(filename='io/philharmonic.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        log("\n-------------\nPHILHARMONIC\n-------------")
        self.start = datetime.now()
        time.sleep(5) # give ourselves time to start the benchmark
        log("#scheduler#start %s" % str(self.start))
        
    def finalize(self):
        self.end = datetime.now()
        log("#scheduler#end %s" % str(self.end))
        self.duration = self.end - self.start
        log("#scheduler#runtime %s" % str(self.duration))
        self.results = {"start":self.start, "end":self.end, "duration":self.duration}
        with open(conf.results, "wb") as results_file:
            pickle.dump(self.results, results_file)
        log("------------------\n")
        
    def run(self):
        self.initialize()
        while True:
            if self.benchmark_done():
                print("benchmark done")
                break
            time.sleep(conf.sleep_interval)
        self.finalize()
