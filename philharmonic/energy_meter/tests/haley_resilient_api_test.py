'''
Created on Nov 12, 2012

@author: kermit
'''
import unittest

from philharmonic.energy_meter.haley_api import Wattmeter
from philharmonic.energy_meter.exception import *

def _dummy_query(self, prefix, identifier):
    self.test_recovery_count += 1
    raise SilentWattmeterError

def _dummy_sleep_time(self, attempts):
        return 0.1

class Test(unittest.TestCase):


    def setUp(self):
        self.meter = Wattmeter()
        self.old_query_method = Wattmeter._query
        Wattmeter._query = _dummy_query
        self.meter.test_recovery_count = 0
        self.meter.max_recoveries = 2
        self.meter._wait_time = 0.1
        self.meter._retries_num = 2
        Wattmeter._sleep_time = _dummy_sleep_time

    def tearDown(self):
        Wattmeter._query = self.old_query_method
        del self.meter

    def test_resilient_query(self):
        tries = 0
        try:
            while True:
                self.meter.measure_single("snowwhite", "active_power")
        except SilentWattmeterError:
            tries = self.meter.test_recovery_count
        self.assertEqual(tries, self.meter.max_recoveries, "expecting several tries")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_resilient_query']
    unittest.main()