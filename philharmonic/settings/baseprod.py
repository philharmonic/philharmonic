from .multicore import *

# if True, will go for the larger simulation
#production_settings = False
production_settings = True

if production_settings:
    show_cloud_interval = pd.offsets.Day(1)
    base_output_folder = os.path.join(common_output_folder,
                                      "results/large_scale/")
    # - one week
    times = pd.date_range(start, periods=24 * 7, freq='H')
    end = times[-1]
    # servers
    inputgen_settings['server_num'] = 2000
    inputgen_settings['min_server_cpu'] = 4
    inputgen_settings['max_server_cpu'] = 4
    inputgen_settings['min_server_ram'] = 16
    inputgen_settings['max_server_ram'] = 32
    # VMs
    inputgen_settings['VM_num'] = 2000
    inputgen_settings['min_cpu'] = 1
    inputgen_settings['max_cpu'] = 4
    inputgen_settings['min_ram'] = 8
    inputgen_settings['max_ram'] = 16
    inputgen_settings['min_duration'] = 60 * 60 # 1 hour
    inputgen_settings['max_duration'] = 60 * 60 * 24 * 7 # 7 days
    #inputgen_settings['max_duration'] = 60 * 60 * 24 * 90 # 90 days
