from nose.tools import *
from mock import MagicMock

from philharmonic import Schedule
from philharmonic.scheduler import BruteForceScheduler
from philharmonic.simulator.environment import FBFSimpleSimulatedEnvironment

def test_fbf_returns_schedule():
    scheduler = BruteForceScheduler()
    scheduler.environment = FBFSimpleSimulatedEnvironment()
    scheduler.environment.get_requests = MagicMock(return_value = [])
    scheduler.environment.get_time = MagicMock(return_value = 1)
    scheduler.cloud = MagicMock()
    schedule = scheduler.reevaluate()
    assert_is_instance(schedule, Schedule)
