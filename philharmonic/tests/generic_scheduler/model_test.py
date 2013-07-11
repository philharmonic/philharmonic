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

    def test_state(self):
        import copy
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        vm2 = VM(1000, 1);
        vm3 = VM(1000, 1);
        VMs = [vm1,vm2,vm3]
        s1.alloc.add(vm1)
        s2.alloc.add(vm2)
        s2.alloc.add(vm3)
        a = State(servers, VMs)
        b = copy.deepcopy(a)
        b.servers[0].alloc.remove(vm1)
        self.assertIn(vm1, a.servers[0].alloc, 'changing one state must not affect the other')

    def test_migration(self):
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        VMs = [vm1]
        
        # initial position
        s1.alloc.add(vm1)
        
        a = State(servers, VMs)
        migr = Migration(vm1, s2)
        b = a.transition(migr)
        self.assertIn(vm1, b.servers[1], 'vm1 should have moved after the transition')
        #TODO: refactor - alloc should be in state!!!
        print(b)
        
        #self.assertIn(vm1, b.servers[s2].alloc, 'VM should be on s2 in state b')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()