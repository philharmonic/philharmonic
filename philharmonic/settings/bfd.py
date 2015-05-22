from .baseprod import *

output_folder = os.path.join(base_output_folder, "bfd/")

factory['scheduler'] = "BFDScheduler"

power_model = "multicore"
