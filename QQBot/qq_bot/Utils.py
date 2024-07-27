import binascii
from base64 import b64encode, b64decode


def encode(string: str):
    string = string.encode('Utf-8')
    string = b64encode(string)
    return string.decode('Utf-8')


def decode(string: str):
    string = string.encode('Utf-8')
    try:
        string = b64decode(string)
    except binascii.Error:
        return None
    return string.decode('Utf-8')
