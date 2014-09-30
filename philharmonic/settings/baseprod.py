from .base import *

# if True, will go for the larger simulation
#production_settings = False
production_settings = True

if production_settings:
    base_output_folder = os.path.join(common_output_folder, "results/summer/")
    times = pd.date_range(start, periods=24 * 90, freq='H')
    end = times[-1]
    factory['times'] = "times_from_conf"
    inputgen_settings['VM_num'] = 2000
    inputgen_settings['min_duration'] = 60 * 60 # 1 hour
    inputgen_settings['max_duration'] = 60 * 60 * 24 * 90 # 90 days
