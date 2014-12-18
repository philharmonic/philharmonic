from .baseprod import *

output_folder = os.path.join(base_output_folder, "bcffs/")

freq_breaks_after_nonfeasible = True

factory['scheduler'] = "BCFFSScheduler"

inputgen_settings['VM_request_generation_method'] = \
    'uniform_vmreqs_beta_variation'
