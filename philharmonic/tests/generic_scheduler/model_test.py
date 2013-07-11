'''
Created on Jul 11, 2013

@author: kermit
'''
import unittest

from philharmonic.scheduler.generic.model import *

class Test(unittest.TestCase):


    def test_constraints(self):
        Machine.resource_types = ['RAM', '#CPUs']
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = set([s1, s2])
        # some VMs
        vm1 = VM(2000, 1);
        vm2 = VM(2000, 2);
        VMs = set([vm1, vm2])
        
        # allocate and check capacity and allocation
        s1.alloc.add(vm1)
        self.assertEqual(all_within_capacity(servers), True, 'all servers within capacity')
        self.assertEqual(all_allocated(servers, VMs), False, 'not all VMs are allocated')
        
        s1.alloc.add(vm2)
        self.assertEqual(all_within_capacity(servers), False, 'not all servers within capacity')
        self.assertEqual(all_allocated(servers, VMs), True, 'all VMs are allocated')
        
        s1.alloc.remove(vm2)
        s2.alloc.add(vm2)
        self.assertEqual(all_within_capacity(servers), True, 'all servers within capacity')
        self.assertEqual(all_allocated(servers, VMs), True, 'all VMs are allocated')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()