'''
Created on Oct 10, 2012

@author: kermit
'''
import threading
import subprocess

class RemoteBenchmark(threading.Thread):
    '''
    A remote benchmark that's being executed on a different (virtual) server
    '''


    def __init__(self, command):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        self.command = command
        pass
    
    def run(self):
        resp = subprocess.call(self.command)
        return resp