import logging
from logging import info, debug, error

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

def log(message):
    print(message)
    logging.info(message)
