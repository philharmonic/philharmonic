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

def _setup(conf_module='philharmonic.settings.base'):
    """initially load which module will be used as philharmonic.conf"""
    globals()['conf'] = import_module(conf_module)
    # default data generators
    global inputgen
    import philharmonic.simulator.inputgen as inputgen
    from philharmonic import conf
    conf.scheduler
