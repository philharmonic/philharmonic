from .baseprod import *

output_folder = os.path.join(base_output_folder, "bcffs/")

freq_breaks_after_nonfeasible = False

factory['scheduler'] = "BCFFSScheduler"
factory['forecast_periods'] = 1 # we make decisions at runtime

power_model = "multicore"

inputgen_settings['VM_request_generation_method'] = \
    'uniform_vmreqs_beta_variation'
    #'auto_vmreqs_beta_variation'
    #'uniform_vmreqs_beta_variation'

# 1 to generate beta, 2 to read them directly from file and
# 3 for all beta equal to fixed_beta_value
inputgen_settings['beta_option'] = 1
inputgen_settings['fixed_beta_value'] = 0.1
inputgen_settings['max_cloud_usage'] = 0.8
