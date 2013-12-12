import threading
import logging
from Queue import Empty
import time
from datetime import datetime
import pickle

from imanager import IManager
from philharmonic.logger import log
from philharmonic import conf

class Manager(IManager, threading.Thread):
    """A real implementation of an IManager"""

    _initial_sleep = 5

    factory = {
        "scheduler": None,
        "environment": None, #TODO
        "cloud": None, #TODO
        "driver": None #TODO
    }

    #TODO: factory has to be - specifiable in the conf and in unittests directly
    #- maybe using mock patching

    def __init__(self):
        '''
        IManager creates the assets, I start the thread.

        '''
        IManager.__init__(self)
        threading.Thread.__init__(self)
        pass


    def initialize(self):
        #logging.basicConfig(filename='io/philharmonic.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        log("\n-------------\nPHILHARMONIC\n-------------")
        self.start = datetime.now()
        self.scheduler.initialize()
        time.sleep(self._initial_sleep) # give ourselves time to start the benchmark
        log("#scheduler#start %s" % str(self.start))
        #TODO: as much logging as possible in the manager

    def benchmark_done(self):
        try:
            self.results = self.q.get_nowait()
            return True  # benchmark done, we got the results
        except Empty:  # benchmark still executing
            return False

    def finalize(self):
        self.end = datetime.now()
        log("#scheduler#end %s" % str(self.end))
        self.duration = self.end - self.start
        log("#scheduler#runtime %s" % str(self.duration))
        self.scheduler.finalize()
        self.results = {"start": self.start, "end": self.end,
                        "duration": self.duration}
        with open(conf.results, "wb") as results_file:
            pickle.dump(self.results, results_file)
        log("------------------\n")

    def run(self):
        self.initialize()
        while True:
            if self.benchmark_done():
                print("benchmark done")
                break
            self.scheduler.reevaluate()
            time.sleep(conf.sleep_interval)
        self.finalize()


from philharmonic.scheduler import PeakPauser, NoScheduler
from philharmonic.cloud.driver.openstack import console_api

class PeakPauserManager(Manager):
    factory = {
        "scheduler": PeakPauser,
        "environment": None, #TODO
        "cloud": None, #TODO
        "driver": console_api #TODO
    }

class NoSchedulerManager(Manager):
    factory = {
        "scheduler": NoScheduler,
        "environment": None, #TODO
        "cloud": None, #TODO
        "driver": console_api #TODO
    }
