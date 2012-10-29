'''
Created on 25. 10. 2012.

@author: kermit
'''

_KWH_RATIO = 3.6e6

def calculate_price(energy_data, price_file):
    pass

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