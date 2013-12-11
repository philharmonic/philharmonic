import unittest
from mock import Mock

from philharmonic.manager import ManagerFactory

class ManagerFactoryTest(unittest.TestCase):

    def test_create_from_conf(self):
        conf = Mock()
        conf.scheduler = "PeakPauser"
        conf.manager = "Simulator"
        manager = ManagerFactory.create_from_conf(conf)
        self.assertIsNotNone(manager)
