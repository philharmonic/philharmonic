'''
Created on Oct 15, 2012

@author: kermit
'''
from datetime import datetime
import math

import philharmonic.timeseries.historian as historian

class EnergyPredictor(object):
    '''
    Represents the energy price
    '''

    def parse(self, price_file):
        self.prices = historian.parse_prices(price_file)
        #print(self.prices.head(30))

    def _find_expensive_hours(self, m):
        """ find the top m*100% most expensive hours
        @param m: the percentage of hours to exclude
        @return: list of expensive hours
        """
        # group hours by hour
        grouped_hours = self.prices.groupby(lambda t : t.hour)
        # how many of the 24 hours exactly
        exclude_num = int(math.ceil(m*24))
        print("We're gonna exclude %d hour(s)" % (exclude_num))
        # we have to make a copy to be able to sort in place
        mean_prices = grouped_hours.mean().copy()
        mean_prices.sort()
        expensive_prices = mean_prices[-exclude_num:]
        self.expensive_hours = set(expensive_prices.index)

    def __init__(self, price_file, percentage_to_pause = 0.15):
        '''
        Constructor
        '''
        #self.price_file = price_file
        self.parse(price_file)
        self._find_expensive_hours(m = percentage_to_pause)
        print("Expensive hours:")
        print(self.expensive_hours)
        self.fig_location = "/home/kermit/Downloads"

    def is_expensive(self, time = None):
        ''' tells if price is expensive now or at time
        @return: bool
        '''
        if not time:
            time = datetime.now()
        return time.hour in self.expensive_hours
