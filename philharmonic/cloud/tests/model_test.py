'''
Created on Jul 11, 2013

@author: kermit
'''
import unittest

from philharmonic import *

class Test(unittest.TestCase):


    def test_constraints(self):
        Machine.resource_types = ['RAM', '#CPUs']
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        vm2 = VM(2000, 2);
        VMs = [vm1, vm2]
        a = State(servers, VMs, auto_allocate=False)

        # allocate and check capacity and allocation
        a.place(vm1,s1)
        self.assertEqual(a.all_within_capacity(), True, 'all servers within capacity')
        self.assertEqual(a.all_allocated(), False, 'not all VMs are allocated')

        a.place(vm2, s1)
        self.assertEqual(a.all_within_capacity(), False, 'not all servers within capacity')
        self.assertEqual(a.all_allocated(), True, 'all VMs are allocated')

        a.remove(vm2, s1)
        a.place(vm2, s2)
        self.assertEqual(a.all_within_capacity(), True, 'all servers within capacity')
        self.assertEqual(a.all_allocated(), True, 'all VMs are allocated')

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
        a = State(servers, VMs, auto_allocate=False)
        a.place(vm1, s1)
        a.place(vm2, s2)
        a.place(vm3, s2)
        b = a.copy()
        b.remove(vm1, s1)
        self.assertIn(vm1, a.alloc[s1], 'changing one state must not affect the other')

    def test_migration(self):
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        VMs = [vm1]

        a = State(servers, VMs)
        # initial position
        a.place(vm1, s1)
        migr = Migration(vm1, s2)
        b = a.transition(migr)

        self.assertIn(vm1, a.alloc[s1], 'vm1 should be on s1 before transition')
        self.assertNotIn(vm1, a.alloc[s2], 'vm1 should be on s1 before transition')

        self.assertNotIn(vm1, b.alloc[s1], 'vm1 should have moved after the transition')
        self.assertIn(vm1, b.alloc[s2], 'vm1 should have moved after the transition')

    def test_pause(self):
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        VMs = [vm1]

        a = State(servers, VMs)
        # initial position
        a.place(vm1, s1)
        pause = Pause(vm1)
        b = a.transition(pause)

        self.assertNotIn(vm1, a.paused,
                         'vm1 should not be paused before transition')
        self.assertIn(vm1, b.paused,
                         'vm1 should be paused after transition')


    def test_cloud(self):
        # some servers
        s1 = Server(4000, 2)
        s2 = Server(8000, 4)
        servers = [s1, s2]
        # some VMs
        vm1 = VM(2000, 1);
        vm2 = VM(2000, 2);
        VMs = [vm1, vm2]
        cloud = Cloud(servers, VMs)
        #TODO: test that auto_allocate doesn't break constraints
        self.assertEqual(cloud.vms, VMs)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
