import logging
from logging import info, debug, error

# log to console
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# log to file
logging.basicConfig(filename='io/philharmonic.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

def log(message):
    logging.info(message)
