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
