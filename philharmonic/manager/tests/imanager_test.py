import unittest
from mock import Mock

from philharmonic.manager import IManager

class MockScheduler(object):
    def __init__(self):
        pass

class IManagerTest(unittest.TestCase):

    def test_empty_factory(self):
        manager = IManager()
        self.assertIs(manager.scheduler, None)
        self.assertIs(manager.environment, None)
        self.assertIs(manager.cloud, None)

    def test_nonempty_factory(self):
        IManager.factory['scheduler'] = MockScheduler
        manager = IManager()
        self.assertIsInstance(manager.scheduler, MockScheduler)
