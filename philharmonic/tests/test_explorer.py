from mock import patch
from nose.tools import *

import pandas as pd

import philharmonic

@patch('philharmonic.simulator.simulator.run')
def test_explore_ga_weights(mock_run):
    philharmonic._setup('philharmonic.settings.ga_explore')
    from philharmonic import conf
    conf.parameter_space = 'GAWeights'
    from philharmonic.explorer import explore
    mock_run.return_value = {'Total cost ($)': 0.5}
    with patch.object(philharmonic.explorer, '_serialise_results',
                      return_value=None) as mock_serialise:
        explore()

@patch('philharmonic.simulator.simulator.run')
def test_explore_time_offsets(mock_run):
    philharmonic._setup('philharmonic.settings.ga_explore')
    from philharmonic import conf
    conf.parameter_space = 'TimeOffsets'
    from philharmonic.explorer import explore
    mock_run.return_value = {'Total cost ($)': 0.5}
    with patch.object(philharmonic.explorer, '_serialise_results',
                      return_value=None) as mock_serialise:
        explore()

def test_time_offsets():
    philharmonic._setup('philharmonic.settings.ga_explore')
    from philharmonic import conf
    conf.start = pd.Timestamp('2010-06-03 00:00')
    conf.times = pd.date_range(conf.start, periods=3, freq='H')
    conf.end = conf.times[-1]
    conf.time_offsets_step = pd.offsets.DateOffset(months=2)
    conf.time_offsets_start = pd.offsets.Hour(0) # the offset of the first run
    conf.time_offsets_max = pd.offsets.DateOffset(months=11, days=20)
    from philharmonic.explorer import TimeOffsets
    combinations = TimeOffsets().combinations
    assert_equals(combinations.shape, (6, 2))
