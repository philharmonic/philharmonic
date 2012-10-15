'''
Created on Oct 15, 2012

@author: kermit
'''
import unittest
from philharmonic.scheduler.energy_price import EnergyPrice


class Test(unittest.TestCase):


    def setUp(self):
        loc = "../io/energy_price_data-test.csv"
        self.energy_price = EnergyPrice(loc)


    def tearDown(self):
        del self.energy_price


    def testEnergyPrice(self):
        from datetime import datetime
        # now - get anything without raising some Errorb
        self.energy_price.is_expensive(datetime.now())
        # morning - cheap price
        time_morning = datetime.strptime("2012-05-05-06-34", "%Y-%m-%d-%H-%M")
        price1 = self.energy_price.is_expensive(time = time_morning)
        self.assertEqual(price1, False, "price must be low at this time")
        # afternoon - expensive
        time_afternoon = datetime.strptime("2012-05-05-17-16", "%Y-%m-%d-%H-%M")
        price2 = self.energy_price.is_expensive(time_afternoon)
        self.assertEqual(price2, True, "price must be high at this time")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEnergyPrice']
    unittest.main()