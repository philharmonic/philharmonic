'''
Created on Oct 9, 2012

@author: kermit
'''

import time
from Queue import Queue, Empty

import conf
from benchmark import Benchmark
from energy_price import EnergyPrice

class PeakPauser(object):
    def __init__(self):
        self.paused=False
        pass

    def parse_prices(self, location):
        self.energy_price = EnergyPrice(location)
    
    def price_is_expensive(self):
        return self.energy_price.is_expensive()
    
    def commence_benchmark(self, command, scripted):
        self.q = Queue() # this is where we'll get the messages from
        benchmark = Benchmark(command, scripted)
        benchmark.q = self.q
        benchmark.start()
        print("started benchmark")
    
    def benchmark_done(self):
        try:
            self.results = self.q.get_nowait()
            return True # benchmark done, we got the results 
        except Empty: # benchmark still executing
            return False
        
    def pause(self):
        if not self.paused:#TODO: pause
            self.paused = True
            print("paused")
    
    def unpause(self):
        if self.paused:#TODO: unpause
            print("unpaused")
            self.paused = False
        
    
    def run(self):
        self.parse_prices(conf.historical_en_prices_file)
        self.commence_benchmark(conf.command, conf.scripted)
        while True:
            if self.benchmark_done():
                print("benchmark done")
                break
            if self.price_is_expensive():
                self.pause()
            elif self.paused:
                self.unpause()
            
            time.sleep(conf.sleep_interval)

if __name__=="__main__":
    scheduler = PeakPauser()
    scheduler.run()
