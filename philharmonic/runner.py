'''
Created on 5. 11. 2012.

@author: kermit
'''
from philharmonic.scheduler.peak_pauser import PeakPauser
from Queue import Queue
import conf
from philharmonic.benchmark import Benchmark

def run(scheduler):
    """
    run experiment, controlled by the scheduler
    """
    # start scheduler
    q = Queue() #TODO: push queue responsibility into IScheduler -> scheduler.quit()
    scheduler.q = q 
    scheduler.start()
    
    # start benchmark
    benchmark = Benchmark(conf.command, scripted=not conf.dummy)
    benchmark.run()
    
    # stop scheduler
    q.put("quit")
    scheduler.join()

if __name__=="__main__":
    scheduler = PeakPauser()
    run(scheduler)
