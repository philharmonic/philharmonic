from mock import patch
from nose.tools import *

import philharmonic

@patch('philharmonic.simulator.simulator.run')
def test_prun(mock_run):
    conf_module = 'philharmonic.settings.ga_profile'
    philharmonic._setup(conf_module)
    mock_run.return_value = True
    from philharmonic import profiler
    profiler.prun('profiler.profile(conf_module={})'.format(conf_module),
                  globals(), locals())
