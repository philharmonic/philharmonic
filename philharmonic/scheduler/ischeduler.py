'''
Created on 5. 11. 2012.

@author: kermit
'''

from philharmonic.logger import log

class IScheduler():
    '''
    Scheduler interface
    '''

    def __init__(self, cloud=None, driver=None):
        '''
        Constructor - scheduler may be created before everything starts running

        '''
        self.cloud = cloud
        self.driver = driver

    def initialize(self):
        '''Hook to start any necessary preparations (VM resets etc.)'''
        raise NotImplemented

    def finalize(self):
        '''Hook to wrap it all up (put VMs back to the default state etc.)'''
        raise NotImplemented

    def reevaluate(self):
        '''Look at the current state of the Cloud and Environment
        and schedule new/different actions if necessary.

        '''
        raise NotImplemented


class NoScheduler(IScheduler):

    def __init__(self):
        # call IScheduler's constructor
        #super(PeakPauser, self).__init__()
        IScheduler.__init__(self)

    def initialize(self):
        pass

    def finalize(self):
        pass

    def reevaluate(self):
        pass
