'''
Created on Oct 22, 2012

@author: kermit
'''
import unittest
from philharmonic.energy_price import historian
import pandas as pd
from datetime import datetime
class Test(unittest.TestCase):


    def testParseHourly(self):
        prices = historian.parse_prices("./io/tests/energy_price_data-test.csv")
        self.assertIs(type(prices), pd.Series, "must get a time series")
        expected_start = datetime(2012,5,5)
        self.assertEqual(prices.index[0][0], expected_start, "expecting to start on this date")
        self.assertEqual(prices.index[1][0], expected_start, "expecting to continue on this date")
        expected_end = datetime.strptime("2012-09-04", "%Y-%m-%d")
        self.assertEqual(prices.index[-1][0], expected_end, "expecting to end on this date")
        
    def testRealign(self):
        prices = historian.parse_prices("./io/tests/energy_price_data-test.csv")
        prices = historian.realign(prices, datetime(2012,5,8))
        expected_start = datetime(2012,5,8)
        self.assertEqual(prices.index[0][0], expected_start, "expecting to start on this date")
        self.assertEqual(prices.index[1][0], expected_start, "expecting to continue on this date")
        expected_end = datetime.strptime("2012-09-07", "%Y-%m-%d")
        self.assertEqual(prices.index[-1][0], expected_end, "expecting to end on this date")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testParseHourly']
    unittest.main()