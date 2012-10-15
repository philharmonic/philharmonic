'''
Created on 14. 9. 2012.

@author: kermit
'''

from datetime import datetime
import numpy as np
import os
import pandas as pd

def parse_prices(where):
    """
    @param where: path to price file location (format as downloadable from
    [here](https://www2.ameren.com/RetailEnergy/rtpDownload.aspx).
    @return a Pandas Series
    """
    # parse file
    with open(os.path.expanduser(where)) as input_file:
        lines = list(input_file)
        prices = []
        for line in lines[1:]:
            date, hour, price = line.rstrip().split(",")
            date = datetime.strptime(date, "%Y-%m-%d")
            hour, price = int(hour), float(price)
            prices.append((date, hour, price))
    # into np array
    prices_only = np.array([el[2] for el in prices])
    hours_only = np.array([el[1] for el in prices])
    dates_only = np.array([el[0] for el in prices])
    # and then a pandas time series
    index_tuples = [(el[0],el[1]) for el in prices]
    multi_index = pd.MultiIndex.from_tuples(index_tuples, names = ["days", "hours"])
    s = pd.Series(prices_only, index = multi_index)
    return s
    
if __name__ == "__main__":
    path = "/home/kermit/Dropbox/dev/itd/skripte/ipy_notebook/data/DAData_19_20120505-20120904.csv"
    prices = parse_prices(path)
    print(prices) 