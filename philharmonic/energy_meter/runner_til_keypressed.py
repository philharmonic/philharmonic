'''
created on Jun 19, 2012

@author: kermit
'''

from Queue import Queue
from getch import _Getch

from continuous_energy_meter import ContinuousEnergyMeter
import conf

class RunnerTilKeypressed(object):
    '''
    Runs a background process until keypressed
    '''


    def __init__(self):
        '''
        Constructor
        '''
        pass

    def run(self, thread):
        '''
        runs thread until user presses a quit-key.
        '''
        q = Queue()
        thread.q = q
        thread.start()
        print('Measurement started. Enter q to quit.')
        inkey = _Getch()
        import sys
        while True:
            k=inkey()
            if k=='q':
                q.put('quit')
                break
        print('you pressed ' + k)
        #import ipdb; ipdb.set_trace()
        thread.join()
        print("Background thread joined.")
        data = q.get()
        return data

def run_once():
    cont_en_meter = ContinuousEnergyMeter(conf.machines, conf.metrics,
                                          conf.interval, conf.location)
    runner = RunnerTilKeypressed()
    data = runner.run(cont_en_meter)
    print(data)

if __name__ == '__main__':
    run_once()
