'''
Created on Sep 4, 2014

@author: kermit

'''

from nose.tools import *

from philharmonic.cloud.visualiser import *

def test_create_usage_str():
    usage = 0.7
    bins = 4
    usage_str = create_usage_str(usage, bins)
    assert_equals(usage_str, '###_')

    usage = 0.3
    bins = 4
    usage_str = create_usage_str(usage, bins)
    assert_equals(usage_str, '##__')

def test_create_usage_str_empty():
    usage = 0.
    bins = 5
    usage_str = create_usage_str(usage, bins)
    assert_equals(usage_str, '_____')

def test_create_usage_str_full():
    usage = 1.
    bins = 6
    usage_str = create_usage_str(usage, bins)
    assert_equals(usage_str, '#' * bins)
