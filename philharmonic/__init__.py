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

# reading experiment measurements
from philharmonic.energy_meter.continuous_energy_meter import deserialize_folder, synthetic_power, build_synth_measurement

# default data generators
import philharmonic.simulator.inputgen as inputgen

def _setup(conf_module):
    """initially load which module will be used as philharmonic.conf"""
    globals()['conf'] = import_module(conf_module)
