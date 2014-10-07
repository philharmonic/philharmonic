import logging
import os

LOG_PATH, LOG_FILENAME = '.', 'philharmonic.log'
LOG_LEVEL = logging.DEBUG

logging.basicConfig(
    level=LOG_LEVEL,
    #format='%(asctime)s  %(message)s',
    format='%(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_PATH, LOG_FILENAME),
            mode='w'
        ), # file output
        logging.StreamHandler() # stdout
    ]
)

from logging import info, debug, error

logging.getLogger().setLevel(LOG_LEVEL)

def log(message):
    logging.info(message)
