'''
Created on Oct 15, 2012

@author: kermit
'''
import unittest
import pandas as pd

from philharmonic.scheduler.energy_predictor import EnergyPredictor
#from philharmonic.energy_price.calculator import *
import philharmonic as ph

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.loc = "./io/tests/energy_price_data-test.csv"
        self.price_predictor = EnergyPredictor(self.loc)
        en_data = pd.read_pickle("./io/tests/energy_consumption.pickle")
        self.active_power = en_data.xs("snowwhite").xs("active_power")

    def tearDown(self):
        del self.price_predictor

    def test_is_expensive(self):
        from datetime import datetime
        # now - get anything without raising some Error
        self.price_predictor.is_expensive(datetime.now())
        # morning - cheap price
        time_morning = datetime.strptime("2012-05-05-06-34", "%Y-%m-%d-%H-%M")
        price1 = self.price_predictor.is_expensive(time = time_morning)
        self.assertEqual(price1, False, "price must be low at this time")
        # afternoon - expensive
        time_afternoon = datetime.strptime("2012-05-05-15-16", "%Y-%m-%d-%H-%M")
        price2 = self.price_predictor.is_expensive(time_afternoon)
        self.assertEqual(price2, True, "price must be high at this time")

    def test_calculate_energy_real_data(self):
        en = ph.calculate_energy(self.active_power)
        self.assertAlmostEqual(en, 35627.631317890715, delta=1000)

    def test_calculate_energy(self):
        # power = 1
        samples = [1]*24
        power = pd.Series(samples, pd.date_range('2013-01-23', periods=len(samples), freq='s'))
        energy = ph.calculate_energy(power)
        self.assertEqual(energy, 24, 'energy not correctly calculated')
        # power = 3 first 12 s, 1 afterwards
        power.ix[:12] = 3
        energy = ph.calculate_energy(power)
        self.assertAlmostEqual(energy, 48, delta=1.0)#'energy not correctly calculated')

    def test_calculate_energy_df(self):
        n = 24
        samples1 = [1] * n
        samples2 = [2] * n
        power = pd.DataFrame({'samples1':samples1, 'samples2':samples2},
                             pd.date_range('2013-01-23', periods=n, freq='s'))
        energy = ph.calculate_energy(power)
        self.assertEqual(energy['samples1'], 24)
        self.assertEqual(energy['samples2'], 48)

    def test_calculate_price_real_data(self):
        total_price = ph.calculate_price(self.active_power, self.loc,
                                      self.active_power.index[0].to_pydatetime())
        self.assertEqual(total_price, 0.00030026175949577949)

    #def test_calculate_price(self):
        #power = pd.Series(pd.date_range())
        #ph.calculate_price(power, prices)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEnergyPrice']
    unittest.main()
