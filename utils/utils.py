import unicodedata


def normalize_unicode(words: str) -> str:
    unicode_words = ""
    for character in unicodedata.normalize("NFD", words):
        if unicodedata.category(character) != "Mn":
            unicode_words += character
    return unicode_words
