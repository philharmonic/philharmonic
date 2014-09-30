from .baseprod import *

output_folder = os.path.join(base_output_folder, "ga/")

gaconf = {
    "population_size": 100,
    "recombination_rate": 0.15,
    "mutation_rate": 0.05,
    "max_generations": 100,
    "random_recreate_ratio": 0.8,
    "no_temperature": False,
    "no_el_price": False,
}

factory['scheduler'] = "GAScheduler"
factory['scheduler_conf'] = gaconf
