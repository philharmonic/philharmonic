# Temporary middle step in the hierarchy
# (to give unittests the freq power_model):
#
#     base <- multicore <- baseprod <- bcf/bcffs/bfd/...
#
# TODO: make unittests independent and put this back in base

from .base import *

power_model = "multicore"

if power_model == "multicore":
    # last value of util. weights should be max power consumption of a core
    utilisation_weights = [-1.362, 2.798, 1.31, 2.8] # p0, p1, p2 for gamma
    power_weights = [1.318, 0.03559, 0.2243, -0.003184, 0.03137,
                     0.0004377, 0.007106]
    #p00, p10, p01, p20, p11, p30, p21 in power model
else: #optional parameters only for multicore
    utilisation_weights = None
    power_weights = None