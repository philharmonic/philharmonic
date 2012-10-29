'''
Created on Oct 15, 2012

@author: kermit
'''
import unittest
import pandas as pd

from philharmonic.scheduler.energy_predictor import EnergyPredictor
from philharmonic.energy_price.calculator import *

class Test(unittest.TestCase):


    def setUp(self):
        self.loc = "./io/tests/energy_price_data-test.csv"
        self.energy_price = EnergyPredictor(self.loc)
        en_data = pd.DataFrame.load("./io/tests/energy_consumption.pickle")
        self.active_power = en_data.xs("snowwhite").xs("active_power")

    def tearDown(self):
        del self.energy_price


    def testEnergyPrice(self):
        from datetime import datetime
        # now - get anything without raising some Error
        self.energy_price.is_expensive(datetime.now())
        # morning - cheap price
        time_morning = datetime.strptime("2012-05-05-06-34", "%Y-%m-%d-%H-%M")
        price1 = self.energy_price.is_expensive(time = time_morning)
        self.assertEqual(price1, False, "price must be low at this time")
        # afternoon - expensive
        time_afternoon = datetime.strptime("2012-05-05-17-16", "%Y-%m-%d-%H-%M")
        price2 = self.energy_price.is_expensive(time_afternoon)
        self.assertEqual(price2, True, "price must be high at this time")
        
    def testEnergy(self):
        en = calculate_energy(self.active_power)
        self.assertEqual(en, 35627.631317890715)
        
        total_price = calculate_price(self.active_power, self.loc, self.active_power.index[0].to_pydatetime())
        self.assertEqual(total_price, 0.00030026175949577949)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEnergyPrice']
    unittest.main()