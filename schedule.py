'''
Created on Oct 15, 2012

@author: kermit
'''
from philharmonic.scheduler.peak_pauser import PeakPauser

if __name__ == "__main__":
    scheduler = PeakPauser()
    scheduler.run()