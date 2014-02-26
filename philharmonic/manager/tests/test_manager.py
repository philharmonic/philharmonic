'''
Created on Oct 16, 2012

@author: kermit
'''
import unittest

from philharmonic.manager.manager import Manager, PeakPauserManager, NoSchedulerManager

from philharmonic.scheduler import PeakPauser, NoScheduler
from philharmonic.scheduler.ischeduler import IScheduler
import philharmonic.conf as my_conf
from philharmonic import runner

def price_is_expensive(self): # our dummy version of the method
    if self.test_state:
        self.test_state = 0
        return True
    else:
        return False

class ManagerTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        my_conf.dummy = True
        my_conf.sleep_interval = 0
        my_conf.historical_en_prices_file = "./io/energy_price_data-test.csv"
        Manager._initial_sleep = 0 # TODO: mock patch

    def test_run(self):
        #scheduler = NoScheduler()
        manager = NoSchedulerManager()
        runner.run(manager)
        manager.q.put("quit")

    #TODO: fix & test PeakPauser as a management scheduler

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
