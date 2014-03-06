from nose.tools import *

from philharmonic.timeseries.util import *

def test_random_time():
    t1 = pd.Timestamp('1978-03-23 01:00')
    t2 = pd.Timestamp('1998-02-15 12:38')
    t = random_time(t1, t2)
    assert_true(t1 <= t <= t2, 'in the middle')
    assert_true(t.minute == 0)

    t = random_time(t1, t2, round_to_hour=False)
    assert_true(t1 <= t <= t2, 'in the middle')

def test_weighted_mean():
    t = pd.datetime.now()
    idx = [t, t + pd.offsets.Hour(4), t + pd.offsets.Hour(6)]
    s = pd.Series([2, 1, 1], idx)
    # 2 - - - -
    # 1       \ - -
    # 0           \  ~ 1.66...
    # 0 1 2 3 4 5 6

    mean = weighted_mean(s)
    assert_almost_equals(mean, 1.666666666666)

    s2 = pd.Series([4, 2, 2],
                   [t, t + pd.offsets.Hour(4), t + pd.offsets.Hour(6)])
    df = pd.DataFrame({'s1': s, 's2': s2}, idx)
    mean = weighted_mean(df)
    assert_almost_equals(mean['s1'], 1.666666666666)
    assert_almost_equals(mean['s2'], 3.333333333333)
