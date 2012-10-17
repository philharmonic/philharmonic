'''
Created on Oct 16, 2012

@author: kermit
'''
import unittest
import types
from philharmonic.scheduler.peak_pauser import PeakPauser
import philharmonic.scheduler.conf as my_conf

def price_is_expensive(self): # our dummy version of the method
    if self.test_state:
        self.test_state = 0
        return True
    else:
        return False 

class Test(unittest.TestCase):


    def testPeakPauser(self):
        my_conf.dummy = True
        my_conf.historical_en_prices_file = "./io/energy_price_data-test.csv"
        scheduler = PeakPauser()
        # we're changing the method dynamically, but could also have subclassed it
        PeakPauser.price_is_expensive = price_is_expensive
        scheduler.test_state = 1
        scheduler.run()
        self.assertEqual(scheduler.paused, False, "when price is cheap (state 0), we want to unpause")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()