'''
Created on Oct 15, 2012

@author: kermit
'''
import unittest
from nose.tools import *
import pandas as pd

from philharmonic.scheduler import EnergyPredictor
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
        power = pd.Series(samples,
                          pd.date_range('2013-01-23', periods=len(samples),
                                        freq='s'))
        energy = ph.calculate_energy(power)
        self.assertEqual(energy, 24, 'energy not correctly calculated')
        # power = 3 first 12 s, 1 afterwards
        power.ix[:12] = 3
        energy = ph.calculate_energy(power)
        self.assertAlmostEqual(energy, 48, delta=1.0)

    def test_calculate_energy_df(self):
        n = 24
        samples1 = [1] * n
        samples2 = [2] * n
        power = pd.DataFrame({'samples1':samples1, 'samples2':samples2},
                             pd.date_range('2013-01-23', periods=n, freq='s'))
        energy = ph.calculate_energy(power)
        self.assertEqual(energy['samples1'], 24)
        self.assertEqual(energy['samples2'], 48)

    def test_calculate_cooling_overhead(self):
        n = 32
        power_samples = [100] * n
        temperature_samples = [15] * (n/2) + [27] * (n/2)
        idx = pd.date_range('2013-01-23', periods=n, freq='s')
        power = pd.Series(power_samples, idx)
        temperature = pd.Series(temperature_samples, idx)
        p_total = ph.calculate_cooling_overhead(power, temperature)
        self.assertTrue((p_total > power).all(), 'cooling adds to power')
        self.assertTrue(p_total[3] < p_total[23], 'colder == more efficient')
    def test_calculate_cooling_overhead_df(self):
        n = 32
        power_samples1 = [100] * n
        power_samples2 = [105] * n
        temperature_samples1 = [15] * (n/2) + [27] * (n/2)
        temperature_samples2 = [-3] * (n/2) + [2] * (n/2)
        idx = pd.date_range('2013-01-23', periods=n, freq='s')
        power = pd.DataFrame({'A': power_samples1, 'B': power_samples2}, idx)
        temperature = pd.DataFrame({'A': temperature_samples1,
                                    'B': temperature_samples2}, idx)
        p_total = ph.calculate_cooling_overhead(power, temperature)
        self.assertTrue((p_total['A'] > power['A']).all(),
                        'cooling adds to power')
        self.assertTrue((p_total['A'] > p_total['B']).all(),
                        'cold places more efficient')
        #self.assertTrue(p_total[3] < p_total[23])

    def test_calculate_price_real_data(self):
        total_price = ph.calculate_price(self.active_power, self.loc,
                                      self.active_power.index[0].to_pydatetime())
        self.assertAlmostEqual(total_price, 0.00030026175949577949)

    #def test_calculate_price(self):
        #power = pd.Series(pd.date_range())
        #ph.calculate_price(power, prices)

def test_calculate_power():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util, 's2': [0.75] * 2 * num})
    power = ph.calculate_power(util, P_idle=100, P_peak=200)
    assert_equals(power['s1'][0], 0)
    assert_equals(power['s1'][num], 150)
    assert_equals(list(power['s1'][:num]), [0] * num)
    assert_equals(list(power['s1'][num:]), [150] * num)
    assert_equals(list(power['s2']), [175] * 2 * num)

def test_calculate_power_freq():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util, 's2': [0.75] * 2 * num})
    power = ph.calculate_power_freq(util, f=2000, P_idle=100, P_base=150,
                                    P_dif=15, f_base=1000)
    assert_equals(list(power['s1'][:num]), [0] * num)
    assert_equals(list(power['s1'][num:]), [132.5] * num)
    assert_equals(list(power['s2']), [148.75] * 2 * num)

def test_calculate_power_freq_different_freqs():
    index = pd.date_range('2013-01-01', periods=6, freq='H')
    num = len(index)/2
    util = pd.Series([0]*num + [0.5]*num, index)
    util = pd.DataFrame({'s1': util, 's2': [0.75] * 2 * num})
    freq = pd.Series([1.]*num + [0.7]*num, index)
    freq  = pd.DataFrame({'s1': freq, 's2': [0.8] * 2 * num})
    freq = freq * 2000
    power = ph.calculate_power_freq(util, freq, P_idle=100, P_base=150,
                                    P_dif=15, f_base=1000)
    assert_equals(list(power['s1'][:num]), [0] * num)
    assert_almost_equals(list(power['s1'][num:]), [125.48] * num)
    assert_almost_equals(list(power['s2']), [139.93] * 2 * num)

def test_vm_price():
    cost = ph.vm_price(2000)
    assert_is_instance(cost, float)
    cost2 = ph.vm_price(3000)
    assert_greater(cost2, cost)

def test_vm_price_progressive():
    cost1 = ph.vm_price_progressive(2000, 1.)
    cost2 = ph.vm_price_progressive(3000, 1.)
    cost3 = ph.vm_price_progressive(2000, .5)
    cost4 = ph.vm_price_progressive(2000, 0)
    cost5 = ph.vm_price_progressive(3000, 0)
    assert_greater(cost2, cost1)
    assert_greater(cost3, cost1)
    assert_equals(cost4, cost5)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEnergyPrice']
    unittest.main()
