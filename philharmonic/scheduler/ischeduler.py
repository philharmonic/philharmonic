'''
Created on 5. 11. 2012.

@author: kermit
'''

import threading

class IScheduler(threading.Thread):
    '''
    Scheduler interface
    '''


    def __init__(self):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        pass
    
    def run(self):
        raise NotImplementedError
        