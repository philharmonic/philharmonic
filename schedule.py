'''
Created on Oct 15, 2012

@author: kermit
'''
from philharmonic.scheduler.peak_pauser import PeakPauser
import sys
from datetime import datetime
import time

if __name__ == "__main__":
    scheduler = PeakPauser()
    # waiting for the start time
    if len(sys.argv)>1:
        when = datetime.strptime(sys.argv[1], "%Y-%m-%d_%H:%M")
        #to_start = datetime.combine(datetime.now().date(), when.time())
        to_start = when
        print("will start at %s." % to_start)
        while datetime.now()<to_start:
            time.sleep(1)
    # start
    scheduler.run()
