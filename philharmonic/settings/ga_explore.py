from .ga import *

output_folder = os.path.join(base_output_folder, "ga_explore/")
prompt_configuration = False

gaconf["greedy_constraint_fix"] = True
gaconf["always_greedy_fix"] = True
gaconf["population_size"] = 1
gaconf["max_generations"] = 1

# exploration range

w_util_min, w_util_max = 0., 1.
w_cost_min, w_cost_max = 0., 1.
w_sla_min, w_sla_max = 0., 1.
w_constraint_min, w_constraint_max = 0., 1.
resolution = 0.1
