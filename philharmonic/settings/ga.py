from .baseprod import *

output_folder = os.path.join(base_output_folder, "ga/")

gaconf = {
    #"population_size": 40,
    "population_size": 10,
    "recombination_rate": 0.15,
    "mutation_rate": 0.05,
    #"max_generations": 60,
    "max_generations": 2,
    "random_recreate_ratio": 0.8,
    "no_temperature": False,
    "no_el_price": False,
    # apply a hybrid GA/greedy algorithm, where
    # greedy hard constraint resolution is attempted
    # on the best schedule generated by the GA
    "greedy_constraint_fix": False,
    # apply fix even if there are no constraint violations
    "always_greedy_fix": False,
    # fitness function weights
    "w_util": 0.4,
    "w_cost": 0.4,
    "w_sla": 0.,
    "w_constraint": 0.2,
}

if production_settings:
    gaconf["population_size"] = 100
    gaconf["max_generations"] = 100

factory['scheduler'] = "GAScheduler"
factory['scheduler_conf'] = gaconf
