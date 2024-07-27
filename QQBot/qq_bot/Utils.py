import binascii
from base64 import b64encode, b64decode


def decode(string: str):
    string = string.encode('Utf-8')
    string = b64decode(string)
    return string.decode('Utf-8')


def encode(string: str):
    string = string.encode('Utf-8')
    try:
        string = b64encode(string)
    except binascii.Error:
        return None
    return string.decode('Utf-8')
