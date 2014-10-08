from .base import *

output_folder = os.path.join(base_output_folder, "test/")

prompt_configuration = False
prompt_show_cloud = False

factory['cloud'] = "small_infrastructure"
factory['requests'] = "simple_vmreqs"
    #  simple_el, medium_el, usa_el, world_el, dynamic_usa_el
    #  simple_temperature, medium_temperature, usa_temperature,
    #  world_temperature, dynamic_usa_temp
factory['el_prices'] = "simple_el"
factory['temperature'] = "simple_temperature"

