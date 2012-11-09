'''
Created on 5. 11. 2012.

@author: kermit
'''
from philharmonic.scheduler.peak_pauser import PeakPauser, NoScheduler
from Queue import Queue
import conf
from philharmonic.benchmark import Benchmark

def run(scheduler):
    """
    run experiment, controlled by the scheduler
    """
    # start scheduler
    q = Queue() # this is where we'll get the messages from
    #TODO: push queue responsibility into IScheduler -> scheduler.quit()
    scheduler.q = q 
    scheduler.start()
    
    # start benchmark
    benchmark = Benchmark(conf.command)
    benchmark.run()
    
    # stop scheduler
    q.put("quit")
    scheduler.join()

#if __name__=="__main__":
#    scheduler = getattr(conf.scheduler)
#    run(scheduler)
