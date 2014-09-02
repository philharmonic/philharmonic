import unittest
from mock import Mock
import copy

from philharmonic.manager import IManager
from philharmonic import scheduler

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
        none_factory = copy.copy(IManager.factory)
        scheduler.MockScheduler = MockScheduler
        IManager.factory['scheduler'] = 'MockScheduler'
        manager = IManager()
        self.assertIsInstance(manager.scheduler, MockScheduler)
        IManager.factory = none_factory

    def test_nonempty_factory_explicit(self):
        #factory = copy.copy(IManager.factory)
        factory = IManager.factory_copy()
        factory['scheduler'] = 'MockScheduler'
        manager = IManager(factory)
        self.assertIsInstance(manager.scheduler, MockScheduler)

    def test_immutable(self):
        self.test_empty_factory()
        self.test_nonempty_factory()
        self.test_empty_factory()
