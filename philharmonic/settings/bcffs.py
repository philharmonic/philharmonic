from .baseprod import *

output_folder = os.path.join(base_output_folder, "bcffs/")

# If the scheduler should stop after no freq. decrease was feasible for one
# of the PMs (for performance reasons). This should always be False in the
# current implementation, because freq. resetting should happen as a pre-step
# and this requires more complicated changes to the state transitioning.
freq_breaks_after_nonfeasible = False

factory['scheduler'] = "BCFFSScheduler"
factory['forecast_periods'] = 1 # we make decisions at runtime

inputgen_settings['VM_request_generation_method'] = \
    'auto_vmreqs_beta_variation'
#    'uniform_vmreqs_beta_variation'


# 1 to generate beta, 2 to read them directly from file and
# 3 for all beta equal to fixed_beta_value
inputgen_settings['beta_option'] = 1
inputgen_settings['fixed_beta_value'] = 0.01
inputgen_settings['max_cloud_usage'] = 0.8
