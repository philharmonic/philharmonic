'''
Created on Oct 10, 2012

@author: kermit
'''
import threading
import subprocess


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
        resp = 1 #TODO: put into queue
        # self.q.put(resp)
        return 0
    soap_done.useKeywords = 1

    def soap_deferred(self):
        return defer.succeed(2)

def dummy_benchmark():
    #import time
    #time.sleep(3)
    import SOAPpy
    p = SOAPpy.SOAPProxy('http://localhost:8088/')
    print p.add(a=1)
    print p.add(a=1, b=3)
    print p.echo([1, 2])
    print("Got responseeee: " + p.done("SOME_RESULTS"))


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
            subprocess.call(self.command)
        else: # running something locally
            subprocess.call("ls")#"python philharmonic/scheduler/benchmark.py &")
        self.wait_til_finished()
        
    def wait_til_finished(self):
        reactor.listenTCP(8088, server.Site(BenchmarkWaiter()))
        reactor.run()
        
if __name__=="__main__":
    dummy_benchmark()
