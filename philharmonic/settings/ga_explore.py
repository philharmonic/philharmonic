from .ga import *

output_folder = os.path.join(base_output_folder, "ga_explore/")
prompt_configuration = False

gaconf["greedy_constraint_fix"] = True
gaconf["always_greedy_fix"] = True
gaconf["population_size"] = 1
gaconf["max_generations"] = 1

# exploration range

# - GAWeights
w_util_min, w_util_max = 0., 1.
w_cost_min, w_cost_max = 0., 1.
w_sla_min, w_sla_max = 0., 1.
w_constraint_min, w_constraint_max = 0., 1.
resolution = 0.1

# - TimeOffsets
time_offsets_step = pd.offsets.DateOffset(months=2)
time_offsets_start = pd.offsets.Hour(0) # the offset of the first run
time_offsets_max = pd.offsets.DateOffset(months=11, days=20)

# the method used to vary combinations, one of:
# 'GAWeights', 'TimeOffsets'
#parameter_space = 'GAWeights'
parameter_space = 'TimeOffsets'

if parameter_space == 'TimeOffsets':
    start = pd.Timestamp('2010-01-03 00:00')
    #times = pd.date_range(start, periods=24 * 7, freq='H')
    times = pd.date_range(start, periods=3, freq='H')
    end = times[-1]
