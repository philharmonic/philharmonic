from nose.tools import *

from philharmonic.scheduler.generic.model import Server
from philharmonic.simulator.inputgen import *

def test_small_infrastructure():
    servers = small_infrastructure()
    assert_is_instance(servers, list)
    assert_is_instance(servers[0], Server)
