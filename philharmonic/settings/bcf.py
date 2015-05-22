from .baseprod import *

output_folder = os.path.join(base_output_folder, "bcf/")

factory['scheduler'] = "BCFScheduler"

power_model = "multicore"
