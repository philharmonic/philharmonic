'''
Created on 5. 11. 2012.

@author: kermit
'''

from philharmonic.logger import log

class IScheduler():
    '''
    Scheduler interface
    '''

    def __init__(self, cloud=None):
        '''
        Constructor - scheduler may be created before everything starts running

        '''
        self.cloud = cloud

    def initialize(self):
        '''Hook to start any necessary preparations (VM resets etc.)'''
        pass

    def finalize(self):
        '''Hook to wrap it all up (put VMs back to the default state etc.)'''
        pass

    def reevaluate(self):
        '''Look at the current state of the Cloud and Environment
        and schedule new/different actions if necessary.

        '''
        pass
