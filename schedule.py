'''
Created on Oct 15, 2012

@author: kermit
'''
from philharmonic.manager.manager import ManagerFactory
import sys
from datetime import datetime
import time
from philharmonic import runner
from philharmonic import conf

if __name__ == "__main__":
    # create the cloud manager with the desired modules
    manager = ManagerFactory.create_from_conf(conf)

    # waiting for the start time
    if len(sys.argv)>1:
        when = datetime.strptime(sys.argv[1], "%Y-%m-%d_%H:%M")
        #to_start = datetime.combine(datetime.now().date(), when.time())
        to_start = when
        print("will start at %s." % to_start)
        while datetime.now()<to_start:
            time.sleep(1)
    # start
    runner.run(manager)
