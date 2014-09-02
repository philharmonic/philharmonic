from .base import *

# if True, will go for the larger simulation
#production_settings = False
production_settings = True

end = pd.Timestamp('2010-03-30 23:00')
times = pd.date_range(start, end, freq='H')

if production_settings:
    factory['times'] = "times_from_conf"
    inputgen_settings['VM_num'] = 2000
    inputgen_settings['min_duration'] = 60 * 60 # 1 hour
    inputgen_settings['max_duration'] = 60 * 60 * 24 * 90 # 90 days
