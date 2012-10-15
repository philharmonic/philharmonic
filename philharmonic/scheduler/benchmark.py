'''
Created on Oct 10, 2012

@author: kermit
'''
import threading
import subprocess

class Benchmark(threading.Thread):
    '''
    A remote benchmark that's being executed on a different (virtual) server
    '''


    def __init__(self, command, scripted = True):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        self.command = command
        self.scripted = scripted
        pass
    
    def run(self):
        if self.scripted:
            resp = subprocess.call(self.command)
            #TODO: parse response
        else: # running something locally
            import time
            time.sleep(120)
            resp = 1
        self.q.put(resp)
