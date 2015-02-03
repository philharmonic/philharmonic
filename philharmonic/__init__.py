from importlib import import_module

# generic scheduler stuff
from philharmonic.cloud.model import *
from philharmonic.logger import info, debug, error

# reading temperature and el. price data
from philharmonic.timeseries.historian import *
from philharmonic.timeseries.calculator import *
from philharmonic.timeseries.util import *

# the default conf if nothing is overriden
import philharmonic.settings.base as conf

def _override_model_defaults():
    # set the frequency settings
    Server.freq_scale_max = conf.freq_scale_max
    Server.freq_scale_min = conf.freq_scale_min
    Server.freq_scale_delta = conf.freq_scale_delta
    Server.freq_scale_digits = conf.freq_scale_digits
    # TODO: also set Server.resource_types

def _setup(conf_module='philharmonic.settings.base'):
    """initially load which module will be used as philharmonic.conf"""
    globals()['conf'] = import_module(conf_module)
    # default data generators
    global inputgen
    import philharmonic.simulator.inputgen as inputgen
    from philharmonic import conf
    _override_model_defaults()
