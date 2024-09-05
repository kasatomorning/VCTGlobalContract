from logging import getLogger, StreamHandler, DEBUG


def setup_logger(name):
    logger = getLogger(name)
    logger.setLevel(DEBUG)
    console_handler = StreamHandler()
    console_handler.setLevel(DEBUG)
    logger.addHandler(console_handler)
    return logger
