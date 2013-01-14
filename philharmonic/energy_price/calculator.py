'''
Created on 25. 10. 2012.

@author: kermit
'''

from historian import *

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

def calculate_price(power, price_file, start_date=None, old_parser=False):
    """parse prices from a price_file ($/kWh), realign it to start_date 
    (if it's provided) and calculate the price of the energy consumption 
    stored in a time series of power values power (W)
    
    @return: calculated price in $
    
    """
    prices = parse_prices(price_file)
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

def calculate_energy(power):
    """Calculates an integral of power over time
    using the rectangle method.
    
    @return: calculated energy in Joules
    
    """
    times = power.index
    N = float(len(times) + 1)
    t_0 = times[0]
    # we don't really know when the last interval ended, so we'll make a guess
    t_N = times[-1]+(times[-1]-times[-2])
    duration = (t_N - t_0)
    h = duration.total_seconds()/N
    en = h*sum(power)
    return en

def joul2kWh(jouls):
    """@return: equivalent kWh """
    kWh = jouls / _KWH_RATIO
    return kWh
    
def kWh2joul(kWh):
    """@return: equivalent Jouls """
    jouls = kWh * _KWH_RATIO
    return jouls