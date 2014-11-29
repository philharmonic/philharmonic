'''
Created on 5. 11. 2012.

@author: kermit
'''
from philharmonic.scheduler import NoScheduler
from philharmonic.scheduler.peak_pauser.peak_pauser import PeakPauser
from Queue import Queue
from philharmonic import conf


def start_benchmark():
    from philharmonic.benchmark import Benchmark
    # start benchmark
    benchmark = Benchmark(conf.command)
    benchmark.run()

def run(manager):
    """
    run experiment, controlled by the manager
    """
    # start scheduler
    q = Queue() # this is where we'll get the messages from
    #TODO: push queue responsibility into IScheduler -> scheduler.quit()
    manager.q = q
    manager.start()

    start_benchmark()

    # stop scheduler
    q.put("quit")
    manager.join()
