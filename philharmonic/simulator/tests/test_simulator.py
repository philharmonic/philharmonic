from nose.tools import *

from philharmonic.simulator.simulator import *
from philharmonic.simulator.inputgen import small_infrastructure


def test_run():
    run(steps=3)

def test_server_locations():
    servers = small_infrastructure()
    server_locations(servers, ['location_'+str(s) for s in servers])
    assert_equals(servers[0].loc, 'location_'+str(servers[0]))
    assert_equals(servers[-1].loc, 'location_'+str(servers[-1]))
