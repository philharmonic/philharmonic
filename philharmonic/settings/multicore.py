# Temporary middle step in the hierarchy
# (to give unittests the freq power_model):
#
#     base <- multicore <- baseprod <- bcf/bcffs/bfd/...
#
# TODO: make unittests independent and put this back in base

from .base import *

power_model = "multicore"

if power_model == "multicore":
    if architecture == "arm":
        utilisation_weights = [-1.362, 2.798, 1.31] # p0, p1, p2 for gamma
        power_weights = [1.318, 0.03559, 0.2243, -0.003184, 0.03137,
                         0.0004377, 0.007106]
        performance_factor = 11.
        C_base = C_base / performance_factor
        C_dif_cpu = C_dif_cpu / performance_factor
        C_dif_ram = C_dif_ram / performance_factor
    elif architecture == "intel":
        #Weights to "simulate" no hyperthreading
        #utilisation_weights = [-1.362, 2.798, 1.31] # p0, p1, p2 for gamma
        #power_weights = [38.07, 0.326, 3.105, -0.04085, 0.1133,
        #                 0.004815, 0.0401]

        #Weights to "simulate" hyperthreading --more aggressive
        #utilisation_weights = [-1.362, 2.798, 1.31] # p0, p1, p2 for gamma
        #power_weights = [33.13, 5.015, 4.465, -1.247 , -0.9636,
        #                 0.09825, 0.1999]

        #Weights to "simulate" hyperthreading --less aggressive
        #utilisation_weights = [-1.362, 2.798, 1.31] # p0, p1, p2 for gamma
        #power_weights = [35.76, 2.924, 4.053, -0.7622 , -0.7769,
        #                 0.0661, 0.1776]
        utilisation_weights = [-1.362, 2.798, 1.31] # p0, p1, p2 for gamma
        power_weights = [33.21, 4.568, 4.285, -1.066 , -0.7015,
                      0.08261, 0.1675]

    #p00, p10, p01, p20, p11, p30, p21 in power model

else: #optional parameters only for multicore
    utilisation_weights = None
    power_weights = None
