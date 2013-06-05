'''
Created on 14. 9. 2012.

@author: kermit
'''

from datetime import datetime, time
import numpy as np
import os
import pandas as pd

def parse_prices_old(where):
    """
    @param where: path to price file location (format as downloadable from
    [here](https://www2.ameren.com/RetailEnergy/rtpDownload.aspx).
    @return a Pandas Series
    @deprecated: use parse_prices
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
    index_tuples = [(el[0],el[1]-1) for el in prices]
    multi_index = pd.MultiIndex.from_tuples(index_tuples, names = ["days", "hours"])
    s = pd.Series(prices_only, index = multi_index)
    return s

def parse_prices(where):
    """
    @param where: path to price file location (format as downloadable from
    [here](https://www2.ameren.com/RetailEnergy/rtpDownload.aspx).
    @return a Pandas Series
    """
    def format_hour(hour):
        #print(str(int(hour)-1)+':00')
        return str(int(hour)-1)+':00'
    where = os.path.expanduser(where)
    df = pd.read_csv(where, converters={'HOUR':format_hour}, 
        parse_dates=[['DATE', 'HOUR']], index_col='DATE_HOUR')
    #df.index = df.index - pd.DateOffset(hours=1)
    s = df['PRICE'].asfreq('H')
    s.index.name = 'Time'
    s.name = 'Price'
    return s

def parse_temp(where):
    """
    Parse a CSV with historical hourly temperatures available at
    http://www.ncdc.noaa.gov/cdo-web/ into a pd.TimeSeries
    """
    weather = pd.read_csv(where,skiprows=2, header=None,
                      index_col='Date_HrMn',
                      parse_dates=[['Date', 'HrMn']],
                      names=['USAF', 'NCDC', 'Date', 'HrMn', 'I',
                             'Type', 'QCP', 'Temp', 'Q', 'extra'])
    t = weather['Temp']
    t.index.name = 'Time'
    t.name = 'Temperature'
    return t

def realign_old(prices_series, start_date):
    """
    A function that shifts prices to start on the target date
    @param prices_series: a Pandas time series (MultiIndex, datetime on level 0)
    @return: a time series starting at start_date
    @deprecated: use realign
    """
    start_date = datetime.combine(start_date.date(), time(0,0)) # truncate time
    delta = start_date - prices_series.index[0][0]
    # unstack to turn it into a DataSeries first
    return prices_series.unstack().shift(1, freq=delta).stack()

def realign(prices_series, start_date):
    """
    A function that shifts prices to start on the target date
    @param prices_series: a Pandas time series (MultiIndex, datetime on level 0)
    @return: a time series starting at start_date
    """
    start_date = datetime.combine(start_date.date(), time(0,0)) # truncate time
    delta = start_date - prices_series.index[0]
    # unstack to turn it into a DataSeries first
    return prices_series.shift(1, freq=delta)
    
if __name__ == "__main__":
    path = "/home/kermit/Dropbox/dev/itd/skripte/ipy_notebook/data/DAData_19_20120505-20120904.csv"
    prices = parse_prices(path)
    print(prices.tail(30))
