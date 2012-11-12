'''
Created on Sep 11, 2012

@author: kermit
'''
import unittest
from philharmonic.energy_meter.haley_api import Wattmeter
from pandas import Series

class Test(unittest.TestCase):


    def test_wattmeter(self):
        meter = Wattmeter()
        active_power = meter.measure_single("snowwhite", "active_power")
        self.assertEqual(type(active_power), float, "must be the same.")
        
        #TODO: switch to strings
        data = meter.measure_multiple(["snowwhite", "bashful"], ["active_power", "apparent_power"])
        self.assertEqual(type(data), Series, "must get a data frame")
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_wattmeter']
    unittest.main()