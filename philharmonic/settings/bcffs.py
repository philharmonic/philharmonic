from .baseprod import *

output_folder = os.path.join(base_output_folder, "BCFFS/")

power_freq_model = True

factory['scheduler'] = "BCFFSScheduler"

inputgen_settings['VM_request_generation_method'] = \
    'uniform_vmreqs_beta_variation'
