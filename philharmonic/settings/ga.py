from .baseprod import *

output_folder = "io/results/ga/"

gaconf = {
    "population_size": 100,
    "recombination_rate": 0.15,
    "mutation_rate": 0.05,
    "max_generations": 20,
    "random_recreate_ratio": 0.8,
    "no_temperature": False,
    "no_el_price": False,
}

factory['scheduler'] = GAScheduler
factory['scheduler_conf'] = gaconf
