from .baseprod import *

output_folder = os.path.join(base_output_folder, "bcffs/")

freq_breaks_after_nonfeasible = True

factory['scheduler'] = "BCFFSScheduler"

inputgen_settings['VM_request_generation_method'] = \
    'uniform_vmreqs_beta_variation'

# 1 to generate beta, 2 to read them directly from file and
# 3 for all beta equal to 1
inputgen_settings['beta_option'] = 1
