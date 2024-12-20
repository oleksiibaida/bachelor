import logging

def logger_init(name=__name__, debug = True):
    logging.basicConfig(level=logging.DEBUG,  # Set the minimum logging level to DEBUG
                    format='%(asctime)s - %(filename)s -  %(funcName)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
    return logger    