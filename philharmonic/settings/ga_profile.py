from .ga import *

output_folder = os.path.join(base_output_folder, "ga_hybrid/")

gaconf["greedy_constraint_fix"] = True
gaconf["always_greedy_fix"] = True
gaconf["population_size"] = 40
gaconf["max_generations"] = 60
