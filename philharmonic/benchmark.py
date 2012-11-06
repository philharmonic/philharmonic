'''
Created on Oct 10, 2012

@author: kermit
'''
import threading
import subprocess
import time


from twisted.web import soap, server
from twisted.internet import reactor, defer


class BenchmarkWaiter(soap.SOAPPublisher):
    """Publish two methods, 'add' and 'echo'."""

    def soap_echo(self, x):
        return x

    def soap_add(self, a=0, b=0):
        return a + b
    soap_add.useKeywords = 1
    
    def soap_done(self, results = None):
        print("stopping nowwwww " + results)
        reactor.stop()
        return 0
    soap_done.useKeywords = 1

    def soap_deferred(self):
        return defer.succeed(2)

def dummy_benchmark():
    import SOAPpy
    p = SOAPpy.SOAPProxy('http://localhost:8088/')
    print("I am doing a dummy benchmark! Yeiii :)")
    time.sleep(3)
    try:
        p.done(results="Waiting for IKEA")
    except AttributeError:
        pass


class Benchmark():
    '''
    A remote benchmark that's being executed on a different (virtual) server
    '''


    def __init__(self, command, scripted = True):
        '''
        Constructor
        '''
        self.command = command
        self.scripted = scripted
        pass
    
    def run(self):
        if self.scripted:
            subprocess.call(self.command)
        else: # running something locally
            subprocess.Popen(["python", "philharmonic/benchmark.py"])
        print("started benchmark")
        self.wait_til_finished()
        
    def wait_til_finished(self):
        pass
        reactor.listenTCP(8088, server.Site(BenchmarkWaiter()))
        reactor.run()
        
if __name__=="__main__":
    dummy_benchmark()
