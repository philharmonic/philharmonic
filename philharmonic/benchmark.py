'''
Created on Oct 10, 2012

@author: kermit
'''
import threading
import subprocess
import time

from twisted.web import soap, server
from twisted.internet import reactor, defer

from scheduler.peak_pauser import log
import philharmonic.conf as conf

class BenchmarkWaiter(soap.SOAPPublisher):
    """Publish two methods, 'add' and 'echo'."""

    def soap_echo(self, x):
        return x

    def soap_add(self, a=0, b=0):
        return a + b
    soap_add.useKeywords = 1
    
    def soap_done(self, results=None):
        #dt1, dt2 = results
        #print("stopping nowwwww " + results)
        #log("#scheduler#berserk#runtime %s" % str(dt2-dt1))
        reactor.stop()
        return 0
    soap_done.useKeywords = 1

    def soap_deferred(self):
        return defer.succeed(2)

def dummy_benchmark():
    try:
        import SOAPpy
        p = SOAPpy.SOAPProxy('http://localhost:8088/')
    except:
        pass
    print("I am doing a dummy benchmark! Yeiii :)")
    time.sleep(0.1)
    try:
        p.done(results="Waiting for IKEA")
    except:
        pass


class Benchmark():
    '''
    A remote benchmark that's being executed on a different (virtual) server
    '''


    def __init__(self, command):
        '''
        Constructor
        '''
        self.command = command
    
    def run(self):
        if conf.dummy:
            dummy_benchmark()
        else:
            if self.command == "noscript": # running something locally -> dummy + waiter
                subprocess.Popen(["python", "philharmonic/benchmark.py"])
            else:
                subprocess.call(self.command)
            print("started benchmark")
            self.wait_til_finished()
        
    def wait_til_finished(self):
        reactor.listenTCP(8088, server.Site(BenchmarkWaiter()))
        reactor.run()
        
if __name__=="__main__":
    dummy_benchmark()
