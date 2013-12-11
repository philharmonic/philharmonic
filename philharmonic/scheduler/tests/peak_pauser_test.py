'''
Created on Oct 16, 2012

@author: kermit
'''
import unittest
from philharmonic.scheduler import PeakPauser, NoScheduler
from philharmonic.scheduler.ischeduler import IScheduler
from philharmonic.cloud.driver import nodriver
import philharmonic.conf as my_conf
from philharmonic import inputgen


 #TODO: use mock instead of overriding!
class MockedPeakPauser(PeakPauser):
    def price_is_expensive(self): # our dummy version of the method
        if self.test_state==1: # expensive on first query
            self.test_state = 0
            return True
        else: # cheap afterwards
            return False

class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        my_conf.dummy = True
        my_conf.historical_en_prices_file = "./io/energy_price_data-test.csv"
        IScheduler._initial_sleep = 0.1

    def testPeakPauser(self):
        cloud=inputgen.peak_pauser_infrastructure()
        scheduler = MockedPeakPauser(cloud, driver=nodriver)
        self.assertEqual(scheduler.paused, False,
                         "unpaused initially")
        scheduler.test_state = 1 # expensive
        scheduler.reevaluate()
        self.assertEqual(scheduler.paused, True,
                         "paused when price is expensive (1)")
        # cheap
        scheduler.reevaluate()
        self.assertEqual(scheduler.paused, False,
                         "when price is cheap (state 0), we want to unpause")
        #TODO: check cloud state, not internal variables

    def testNoScheduler(self):
        scheduler = NoScheduler()
        scheduler.test_state = 1 # expensive
        scheduler.reevaluate()
        #TODO: check cloud state

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
