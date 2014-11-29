'''
Created on Oct 16, 2012

@author: kermit
'''
import unittest
from mock import patch

from philharmonic.manager.manager import Manager, PeakPauserManager, \
    NoSchedulerManager

from philharmonic.scheduler.ischeduler import IScheduler
import philharmonic
from philharmonic import conf as my_conf

def price_is_expensive(self): # our dummy version of the method
    if self.test_state:
        self.test_state = 0
        return True
    else:
        return False

class ManagerTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        my_conf.dummy = True
        my_conf.sleep_interval = 0
        my_conf.historical_en_prices_file = "./io/energy_price_data-test.csv"
        Manager._initial_sleep = 0 # TODO: mock patch

    @patch('philharmonic.runner.start_benchmark')
    def test_run(self, mock_bench_run, *args):
        mock_bench_run.return_value = True
        from philharmonic import runner
        manager = NoSchedulerManager()
        runner.run(manager)
        manager.q.put("quit") # <- the manager also does this by itself
        self.assertTrue(manager.results is not None)

    #TODO: fix & test PeakPauser as a management scheduler

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
