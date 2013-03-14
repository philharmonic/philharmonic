'''
Created on 25. 10. 2012.

@author: kermit
'''

from historian import *
from scipy import integrate

_KWH_RATIO = 3.6e6

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

def _calculate_price(power, price, compare_with=None):
    """calculate energy consumption price based on an hourly series
    of prices ($/kWh) and an houlry series of power values (W)
    
    @return: calculated price in $
    
    """
    #TODO: this function assumes hourly mean power aggregation and
    #the ending price at 00:00

    # # optional plotting
    # t = pd.offsets.Day(3)
    # start = P_here.index[0]
    # power[:start+t].plot(color=s1)
    # figure()
    # price[:start + t].plot(color=s2)
    # if not compare_with is None:
    #     figure()
    #     compare_with[:start + t].plot(color=s3)
    
    price = joul2kwh(price[-1])
    #print(len(power))
    #print(len(price))
    #side_by_side(power, price)
    hourly_cost = power * price
    cost = hourly_cost.sum()
    return cost

def calculate_price(power, prices=None, start_date=None, old_parser=False):
    """take or parse from a file a series of electricity prices ($/kWh),
    realign it to start_date (if it's provided) and calculate the price of the
    energy consumption stored in a time series of power values power (W)
    
    @param power: pandas.Series of price values over time or a path to the
    file to be parsed. 
    
    @return: calculated price in $
    
    """
    if type(prices)==str: # let me parse that for you
        prices = parse_prices(prices)
    # Now we say that our energy prices start on this date.
    if start_date:
        prices = realign(prices, start_date)
    prices = per_kwh2per_joul(prices) # convert into $/J
    
    times = list(power.index)
    our_prices_raw = [] # here we'll store prices during the experiment
    for t in times: # TODO: add a changing h value (per hour) and charge per hour
        our_prices_raw.append(prices.asof(t))
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

def calculate_energy(power):
    """Calculates an integral of power over time
    using the rectangle method.
    @param power: pandas.Series of power samples (in Watts) 
    @return: calculated energy in Joules
    
    """
    # manual rectangle rule
#    times = power.index
#    N = float(len(times) + 1)
#    t_0 = times[0]
#    # we don't really know when the last interval ended, so we'll make a guess
#    t_N = times[-1]+(times[-1]-times[-2])
#    duration = (t_N - t_0)
#    h = duration.total_seconds()/N
#    en = h*sum(power)
    # we don't really know when the last interval ended (and at what value), so we'll make a guess
    new_tick = power.index[-1]+(power.index[-1]-power.index[-2])
    power = power.append(pd.Series({new_tick: power[-1]}))
    # calculate the integral
    en = integrate.trapz(power, power.index.astype(np.int64) / 10**9)
    return en

def joul2kwh(jouls):
    """@return: equivalent kWh """
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
