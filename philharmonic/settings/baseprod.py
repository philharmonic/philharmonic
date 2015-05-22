from .multicore import *

# if True, will go for the larger simulation
production_settings = False
#production_settings = True

if production_settings:
    show_cloud_interval = pd.offsets.Day(1)
    base_output_folder = os.path.join(common_output_folder,
                                      "results/large_scale/")
    times = pd.date_range(start, periods=24 * 2, freq='H')
    end = times[-1]
    factory['times'] = "times_from_conf"
    inputgen_settings['VM_num'] = 200
    inputgen_settings['min_duration'] = 60 * 60 # 1 hour
    inputgen_settings['max_duration'] = 60 * 60 * 24 * 2 # 2 days
    #inputgen_settings['max_duration'] = 60 * 60 * 24 * 90 # 90 days
