'''
Created on Oct 9, 2012

@author: kermit
'''

import time
from Queue import Queue, Empty

import conf
from remote_benchmark import RemoteBenchmark

class PeakPauser(object):
    def __init__(self):
        self.paused=False
        pass

    def parse_prices(self, location):
        pass
    
    def price_is_expensive(self):#TODO: implement is_expensive
        return False
    
    def commence_benchmark(self, command):
        self.q = Queue() # this is where we'll get the messages from
        benchmark = RemoteBenchmark(command)
        benchmark.q = self.q
        benchmark.start()
        print("starting benchmark")
    
    def benchmark_done(self):
        try:
            self.results = self.q.get_nowait()
            return True # benchmark done, we got the results 
        except Empty:
            return False
        
    def pause(self):
        print("paused")
    
    def unpause(self):
        print("paused")
    
    def run(self):
        self.parse_prices(conf.historical_en_prices_file)
        self.commence_benchmark(conf.command)
        while True:
            if self.benchmark_done():
                break
            if self.price_is_expensive():
                self.pause()
            elif self.paused:
                self.unpause()
            
            time.sleep(conf.sleep_interval)

if __name__=="__main__":
    scheduler = PeakPauser()
    scheduler.run()
