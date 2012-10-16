'''
Created on Oct 9, 2012

@author: kermit
'''

import time
from Queue import Queue, Empty

import conf
from benchmark import Benchmark
from energy_price import EnergyPrice
import philharmonic.openstack.console_api as openstack

class PeakPauser(object):
    def __init__(self):
        self.paused=False
        openstack.dummy = conf.dummy
        openstack.authenticate()
        

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
        if not self.paused:
            if not conf.dummy:
                openstack.pause(conf.instance)
            self.paused = True
            print("paused")
    
    def unpause(self):
        if self.paused:
            if not conf.dummy:
                openstack.unpause(conf.instance)
            print("unpaused")
            self.paused = False
        
    
    def run(self):
        
        self.parse_prices(conf.historical_en_prices_file)
        self.commence_benchmark(conf.command, scripted = not conf.dummy)
        while True:
            if self.benchmark_done():
                print("benchmark done")
                break
            if self.price_is_expensive():
                self.pause()
            else:
                self.unpause()
            
            time.sleep(conf.sleep_interval)

if __name__=="__main__":
    scheduler = PeakPauser()
    scheduler.run()
