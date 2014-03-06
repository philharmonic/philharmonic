"""Various helpful functions for manipulating time series."""

import random

import pandas as pd
import numpy as np

def random_time(start, end, round_to_hour=True):
    """Random timestamp between start & end
    (optionally rounded to a full hour).

    """
    delta = end - start
    offset = pd.offsets.Second(np.random.uniform(0., delta.total_seconds()))
    t = start + offset
    if round_to_hour:
        t = pd.Timestamp(t.date()) + pd.offsets.Hour(t.hour) # round to hour
    return t

def weighted_mean(data):
    """Data mean weighted on the time durations.

    """
    mean = np.average(data[:-1], weights=np.diff(data.index.asi8), axis=0)
    try:
        mean = pd.Series(mean, data.columns)
    except AttributeError:
        pass # data is a 1-d series -> mean already float
    return mean
