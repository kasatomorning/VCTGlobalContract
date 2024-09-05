import unicodedata
from logging import getLogger, StreamHandler, DEBUG


def setup_logger(name):
    logger = getLogger(name)
    logger.setLevel(DEBUG)
    console_handler = StreamHandler()
    console_handler.setLevel(DEBUG)
    logger.addHandler(console_handler)
    return logger


def normalize_unicode(words: str) -> str:
    unicode_words = ""
    for character in unicodedata.normalize("NFD", words):
        if unicodedata.category(character) != "Mn":
            unicode_words += character
    return unicode_words
