import unittest

from philharmonic import Schedule
from philharmonic.scheduler import FBFScheduler

class FBFSchedulerTest(unittest.TestCase):

    def test_returns_schedule(self):
        scheduler = FBFScheduler()
        schedule = scheduler.reevaluate()
        self.assertIsInstance(schedule, Schedule)
