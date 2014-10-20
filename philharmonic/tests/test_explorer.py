from mock import patch
from nose.tools import *

import philharmonic

@patch('philharmonic.simulator.simulator.run')
def test_explore(mock_run):
    philharmonic._setup('philharmonic.settings.ga_explore')
    from philharmonic.explorer import explore
    mock_run.return_value = {'Total cost ($)': 0.5}
    explore()
