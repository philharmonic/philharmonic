'''
Created on 25. 10. 2012.

@author: kermit

Various functions for calculating energy, costs from power, electricity price,
temperature time series datao. Additionally some functions for converting
currencies etc.
'''

import copy
from datetime import timedelta

from scipy import integrate

from historian import *

_KWH_RATIO = 3.6e6

def calculate_power(util, P_idle=100, P_peak=200):
    """Given a DataFrame of server utilisations, calculate power. This
    model is often used, e.g. in:

    Xu, H., Feng, C., and Li, B. (2013). Temperature aware workload management
    in geo-distributed datacenters. In Proc. USENIX ICAC, 2013.

    """
    P = util * (P_peak - P_idle) # dynamic part
    # a server with no load is suspended (otherwise idle power applies)
    P[P > 0] += P_idle
    return P

def calculate_power_freq(ut, f=2000, P_idle=100, P_base=150,
                         P_dif=15, f_base=1000):
    """Power model as combination of calculate_power and:

    J.-M. Pierson and H. Casanova, "On the Utility of DVFS for Power-Aware Job
    Placement in Clusters", in Euro-Par 2011 Parallel Processing, E. Jeannot,
    R. Namyst, and J. Roman, Eds. Springer Berlin Heidelberg, 2011, pp. 255-266.
    Modelled for f_base=1000, valid for freq.range: 1800-2600 MHz

    """
    P = ut * (P_base + P_dif * ((f - float(f_base)) / f_base)**3 - P_idle)
    # a server with no load is suspended (otherwise idle power applies)
    P[P>0] += P_idle
    return P



# multicore model
##################

# These functions for operating on DataFrames are unused for now,
# since we're calculating the utilisation in model.py, but rethink
# that, as these would be faster.
# def _calculate_core_util_multicore(beta):
#     # model fit from odroid
#     pass

# def _calculate_util_multicore(active_cores, util_beta):
#     # expression with gama (core utilisation)
#     return 0.5 # TODO: finish this
#     c = (active_cores * util_beta).sum(axis=1) / (active_cores.sum(axis=1))
#     return c

def _calculate_peakpower_freq_multicore(
        q, c, p00, p10, p01, p20, p11, p30, p21):
    P=p00+p10*q+p01*c+p20*(q**2)+p11*q*c+p30*(q**3)+p21*(q**2)*c
    return P

# TODO: p00..p30 as some kind of dict or list
def calculate_power_multicore(
        util, freq, active_cores, max_cores, max_capacity=8, freq_abs_min=1800,
        freq_abs_delta=200, p00=2.34, p10=0.598, p01=0.058, p20=-0.16,
        p11=-0.025, p30=0.012, p21=0.01):
    """@param util: utilisation (multicore) based on per-core utilisations
    @param freq: DataFrame of absolute frequencies for servers over time
    @param max_capacity: maximum utilisation in Simon's unitless notation
    (e.g. cores used from 1 to 8, which might not mean the real number of cores)

    """

    # convert to Simon's discrete freq. steps
    try:
        freq_discr = ((freq - freq_abs_min).astype(int) / freq_abs_delta) + 1
    except AttributeError: # it's a scalar - TODO: find more elegant way
        freq_discr = ((freq - freq_abs_min) / freq_abs_delta) + 1
    # utilisation - this is not calculated here right now, but in evaluator.py
    # util = _calculate_util_multicore(active_cores, util_beta)

    # mapping between actual active cores and a discrete parameter
    # for Simon's optimisation
    # c = (active_cores / max_cores) * max_capacity
    c = active_cores
    # peak power when a number of cores are active at a frequency assuming
    # they are fully utilized
    max_power = _calculate_peakpower_freq_multicore(
        freq_discr, c, p00, p10, p01, p20, p11, p30, p21
    )
    # from the model of Holmbacka et al extract the idle part of the power
    idle_power =  _calculate_peakpower_freq_multicore(
        freq_discr, 0, p00, p10, p01, p20, p11, p30, p21
    )
    # take into account the utilization of the active cores
    total_power = idle_power + (max_power - idle_power) * util

    return total_power

##################


def calculate_price_old(power, price_file, start_date=None, old_parser=False):
    """parse prices from a price_file ($/kWh), realign it to start_date
    (if it's provided) and calculate the price of the energy consumption
    stored in a time series of power values power (W)

    @return: calculated price in $

    """
    prices = parse_prices_old(price_file)
    # Now we say that our energy prices start on this date.
    if start_date:
        prices = realign(prices, start_date)
    prices = prices/_KWH_RATIO # convert into $/J

    times = list(power.index)
    our_prices_raw = [] # here we'll store prices during the experiment
    for t in times: # TODO: add a changing h value (per hour) and charge per hour
        our_prices_raw.append(prices[t.date()][t.hour])
    experiment_prices = pd.Series(our_prices_raw, index = power.index)

    times = power.index
    N = float(len(times) + 1)
    t_0 = times[0]
    # we don't really know when the last interval ended, so we'll make a guess
    t_N = times[-1]+(times[-1]-times[-2])
    duration = (t_N - t_0)
    h = duration.total_seconds()/N

    # TODO: use a library for this e.g.
    #   http://docs.scipy.org/doc/scipy/reference/tutorial/integrate.html
    total_price = h * sum(power*experiment_prices)
    return total_price

def calculate_price(power, prices, start_date=None):
    """Take or parse from a file a series of electricity prices ($/kWh),
    realign it to start_date (if it's provided) and calculate the price of the
    energy consumption stored in a time series of power values power (W).
    Should work for DataFrames too.

    @param power: pandas.TimeSeries of power values
    @param prices: pandas.TimeSeries of price values or a path to a
    file to parse it from.
    @param start_date: Timestamp to which to realign the prices
    (e.g. the starting index value for the power series)

    @Return: calculated price in $

    """
    if type(prices)==str: # let me parse that for you
        prices = parse_prices(prices) # TODO: fix for data frames
    # Now we say that our energy prices start on this date.
    if start_date: #TODO: fix for DataFrame
        prices = realign(prices, start_date)
    prices = per_kwh2per_joul(prices) # convert into $/J

    #TODO: replace this with resample() and pass integrate as a function
    # power.resample(prices.index.freq, how=calculate_energy, closed='both')*prices
    #---
    #times = list(power.index)
    #prices_list = [] # here we'll store prices during the experiment
    #for t in times: # TODO: add a changing h value (per hour) and charge per hour
    #    prices_list.append(prices.asof(t))
    prices = prices.reindex(power.index, method='ffill')

    # we don't really know when the last interval ended, so we'll make a guess
    times = power.index
    N = float(len(times) + 1)
    t_0 = times[0]
    t_N = times[-1]+(times[-1]-times[-2])
    duration = (t_N - t_0)
    h = duration.total_seconds()/N
    total_price = h * (power * prices).sum()
    #---
    return total_price

def _calculate_series_energy(power, estimate=False):
    """Calculates energy from a time series fo power values."""
    if estimate: # we won't integrate it
        return power.mean() * len(power.resample('s'))
    # we don't really know when the last interval ended (and at what value),
    # so we'll make a guess
    # TODO: replace this using resample(closed='both')
    new_tick = power.index[-1]+(power.index[-1]-power.index[-2])
    power = power.append(pd.Series({new_tick: power[-1]}))
    # calculate the integral
    en = integrate.trapz(power.values, power.index.astype(np.int64) / 10**9)
    return en

def calculate_energy(power, estimate=False):
    """Calculates the numerical integral of power over time
    using the trapezoidal rule.
    @param power: Series or DataFrame of power samples (in Watts)
    @return: calculated energy in Joules

    """
    if isinstance(power, pd.DataFrame):
        return power.apply(_calculate_series_energy, estimate=estimate)
    if isinstance(power, pd.Series):
        return _calculate_series_energy(power, estimate)

def calculate_cooling_overhead_old(power, temperature):
    """Use a model of cooling overhead and real-time temperatures
    to calculate real-time PUE values and calculate the resulting power.

    source:
    Guler H. (2013). Energy Cost Optimization in Large Scale Distributed Systems
    by Resource Allocation Techniques. Master's thesis.

    """
    # cooling model (Guler)
    #CoP = temperature
    CoP = 1.2 + 0.128 * (temperature + 9)**.5
    CoP = CoP.reindex(power.index, method='ffill')
    return power * CoP
    #return power * CoP

def calculate_pue(temperature):
    pPUE = 7.1705e-5 * temperature**2 + 0.0041 * temperature + 1.0743
    return pPUE

def calculate_cooling_overhead(power, temperature):
    """Use a model of cooling overhead and real-time temperatures
    to calculate real-time PUE values and calculate the resulting power.

    source:
    Xu, H., Feng, C., and Li, B. (2013). Temperature aware workload management
    in geo-distributed datacenters. In Proc. USENIX ICAC, 2013.
    """
    # partial PUE
    pPUE = calculate_pue(temperature)
    #TODO: maybe interpolate values
    pPUE = pPUE.reindex(power.index, method='ffill')
    return power * pPUE

def vm_price(freq, C_base=0.0520278, C_dif=0.018, f_base=1000):
    """Calculate a VM's price based on the frequency. ElasticHosts model."""
    C = C_base + C_dif * (freq - f_base) / f_base
    return C

def vm_price_progressive(freq, beta, C_base=0.0520278, C_dif=0.018,
                         f_base=1000, f_max=3000):
    """Calculate a VM's price based on the frequency and beta, the VM's
    CPU boundedness."""
    C = C_base + C_dif * (beta * freq + (1 - beta) * f_max - f_base) / f_base
    return C

def vm_price_cpu_ram(rel_ram_size, freq, beta, C_base=0.027028, C_dif_cpu=0.018,
                     f_base=1000, f_max=3000, C_dif_ram=0.025):
    """Calculate a VM's price based on the relative memory size, the frequency
    and beta, the VM's CPU boundedness.

    source: http://www.elastichosts.co.uk/calculator:
    modelled for f_max:3000, f_base=1000MHz, RAM size base:1024MB,
    and 20GB HDD and 10 GB Data for the fixed cost of other resources

    """
    C = C_base + \
        C_dif_cpu * (beta * freq + (1 - beta) * f_max - f_base) / f_base + \
        C_dif_ram * rel_ram_size
    return C

def vm_price_multicore(rel_ram_size, active_cores, f_vms, beta_vms, \
                       C_base=0.027028, C_dif_cpu=0.018, \
                       f_base=1000, f_max=3000, C_dif_ram=0.025):
    """Calculate a VM's price based on the relative memory size,
    its number CPU cores, the CPU frequency and beta, the VM's CPU boundedness.

    """
    # cpu_size: cpu used of a VM taking into account beta
    f_cpu = beta_vms * f_vms + (1 - beta_vms) * f_max - f_base
    cpu_size = active_cores * f_cpu / f_base
    # C: overall price of a VM: sum of the cpu cost, the fixed cost and ram cost
    C = C_base + C_dif_cpu * cpu_size + C_dif_ram * rel_ram_size
    return C

def joul2kwh(jouls):
    """@Return: equivalent kWh """
    kWh = jouls / _KWH_RATIO
    return kWh

def kwh2joul(kWh):
    """@return: equivalent Jouls """
    jouls = kWh * _KWH_RATIO
    return jouls

def per_kwh2per_joul(per_kwh):
    """@return: equivalent per Joul"""
    # this is the equiv. of doing:
    return joul2kwh(per_kwh)

def per_joul2per_kwh(per_joul):
    """@return: equivalent per kWh"""
    # this is the equiv. of doing:
    return kwh2joul(per_joul)

def synthetic_power(mean, std, start, end, freq='5s'):
    """build an artificial power time series"""
    index = pd.date_range(start, end, freq='5s', name='Time')
    P_synth = pd.Series(np.random.normal(mean, std, len(index)), index, name='Power')
    P_synth.ix[P_synth < 0] = 0
    return P_synth

def build_synth_measurement(m, P_peak, en_elasticity=0.5,
                            ewma_span=100, uptime=None):
    """build an artificial copy of a Measurement with arbitrary
    peak and idle power values.

    """
    std_peak = m.active_power[m.active_power>40].std()
    P_synth_peak = synthetic_power(P_peak, std_peak, '2012-11-01', '2012-11-10')

    P_idle = P_peak * en_elasticity
    std_idle = m.active_power[m.active_power<40].std()
    P_synth_idle = synthetic_power(P_idle, std_idle, '2012-11-01', '2012-11-10')

    start = m.active_power.index[0]
    end = m.active_power.index[-1]
    pause_start = m.active_power[m.active_power<40].index[0]
    if uptime:
        downtime_ratio = (1-uptime)
        pause_length = 24 * downtime_ratio
        pause_end = pause_start + timedelta(hours=pause_length)
    else:
        pause_end = m.active_power[m.active_power<40].index[-1]
    m_synth = copy.deepcopy(m)
    m_synth.active_power = pd.concat([P_synth_peak[start:pause_start],
                                      P_synth_idle[pause_start:pause_end],
                                      P_synth_peak[pause_end:end]])
    m_synth.ewma_power = pd.ewma(m_synth.active_power, span=ewma_span)

    return m_synth
