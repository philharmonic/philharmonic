'''
Created on Sep 4, 2014

@author: kermit

'''

from nose.tools import *

from philharmonic.cloud.visualiser import *
from philharmonic import *

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

def test_show_cloud_usage():
    Machine.resource_types = ['RAM', '#CPUs']
    # some servers
    s1 = Server(4000, 2, location='Sahara')
    s2 = Server(8000, 4, location='North Pole')
    servers = [s1, s2]
    # some VMs
    vm1 = VM(2000, 1)
    vm2 = VM(2000, 1)
    cloud = Cloud(servers)

    cloud.get_current()
    cloud.apply_real(VMRequest(vm1, 'boot'))
    cloud.apply_real(VMRequest(vm2, 'boot'))
    cloud.apply(Migration(vm1, s1))
    current = cloud.apply(Migration(vm2, s2))
    cloud.show_usage()
