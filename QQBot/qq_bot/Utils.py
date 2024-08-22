import binascii
from base64 import b64encode, b64decode
from json import dumps, loads


def encode(data: dict):
    # 编码
    string = dumps(data, ensure_ascii=False)
    string = string.encode('Utf-8')
    string = b64encode(string)
    return string.decode('Utf-8')


def decode(string: str):
    string = string.encode('Utf-8')
    try:
        string = b64decode(string)
    except binascii.Error:
        return None
    return loads(string.decode('Utf-8'))
