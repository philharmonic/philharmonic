'''
Created on Sep 12, 2012

@author: kermit
'''
import unittest
from philharmonic.energy_meter.continuous_energy_meter import ContinuousEnergyMeter

from pandas import DataFrame
from Queue import Queue
import time

class Test(unittest.TestCase):


    def testWattmeter(self):
        cont_meter = ContinuousEnergyMeter(["snowwhite","happy"], ["active_power", "apparent_power"], 0.1)
        q = Queue()
        cont_meter.q = q
        cont_meter.start()
        #time.sleep(0.)
        cont_meter.q.put("quit")
        cont_meter.join()
        data = cont_meter.get_all_data() 
        self.assertEqual(type(data), DataFrame, "Continuous en. meter must return a data frame")
        #self.assertEqual(len(data.columns), 2, "we expect 2 samples in 2 seconds, but we got %d" % (len(data)))
        self.assertGreaterEqual(len(data.columns), 1, "we expect at least 1 sample in 0.2 seconds")                
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testWattmeter']
    unittest.main()
