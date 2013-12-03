'''
Created on Oct 16, 2012

@author: kermit
'''
import unittest

from philharmonic.manager.manager import Manager

from philharmonic.scheduler.peak_pauser import PeakPauser, NoScheduler
from philharmonic.scheduler.ischeduler import IScheduler
import philharmonic.conf as my_conf
from philharmonic import runner

def price_is_expensive(self): # our dummy version of the method
    if self.test_state:
        self.test_state = 0
        return True
    else:
        return False

class DummyScheduler(IScheduler):
    pass

class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        my_conf.dummy = True
        my_conf.sleep_interval = 0
        my_conf.historical_en_prices_file = "./io/energy_price_data-test.csv"
        Manager._initial_sleep = 0

    def testManager(self):
        dummy_scheduler = DummyScheduler()
        manager = Manager(scheduler=dummy_scheduler)
        runner.run(manager)
        manager.q.put("quit")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
