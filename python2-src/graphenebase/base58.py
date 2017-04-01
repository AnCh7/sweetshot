from binascii import hexlify, unhexlify
import hashlib
import sys
import string
import logging
log = logging.getLogger(__name__)

u""" This class and the methods require python3 """
from __future__ import absolute_import
assert sys.version_info[0] == 3, u"graphenelib requires python3"

u""" Default Prefix """
PREFIX = u"GPH"

known_prefixes = [
    PREFIX,
    u"BTS",
    u"MUSE",
    u"TEST",
    u"STM",
    u"GLX",
    u"GLS",
]


class Base58(object):
    u"""Base58 base class

    This class serves as an abstraction layer to deal with base58 encoded
    strings and their corresponding hex and binary representation throughout the
    library.

    :param data: Data to initialize object, e.g. pubkey data, address data, ...
    :type data: hex, wif, bip38 encrypted wif, base58 string
    :param str prefix: Prefix to use for Address/PubKey strings (defaults to ``GPH``)
    :return: Base58 object initialized with ``data``
    :rtype: Base58
    :raises ValueError: if data cannot be decoded

    * ``bytes(Base58)``: Returns the raw data
    * ``str(Base58)``:   Returns the readable ``Base58CheckEncoded`` data.
    * ``repr(Base58)``:  Gives the hex representation of the data.
    *  ``format(Base58,_format)`` Formats the instance according to ``_format``:
        * ``"btc"``: prefixed with ``0x80``. Yields a valid btc address
        * ``"wif"``: prefixed with ``0x00``. Yields a valid wif key
        * ``"bts"``: prefixed with ``BTS``
        * etc.

    """
    def __init__(self, data, prefix=PREFIX):
        self._prefix = prefix
        if all(c in string.hexdigits for c in data):
            self._hex = data
        elif data[0] == u"5" or data[0] == u"6":
            self._hex = base58CheckDecode(data)
        elif data[0] == u"K" or data[0] == u"L":
            self._hex = base58CheckDecode(data)[:-2]
        elif data[:len(self._prefix)] == self._prefix:
            self._hex = gphBase58CheckDecode(data[len(self._prefix):])
        else:
            raise ValueError(u"Error loading Base58 object")

    def __format__(self, _format):
        u""" Format output according to argument _format (wif,btc,...)

            :param str _format: Format to use
            :return: formatted data according to _format
            :rtype: str

        """
        if _format.upper() == u"WIF":
            return base58CheckEncode(0x80, self._hex)
        elif _format.upper() == u"ENCWIF":
            return base58encode(self._hex)
        elif _format.upper() == u"BTC":
            return base58CheckEncode(0x00, self._hex)
        elif _format.upper() in known_prefixes:
            return _format.upper() + unicode(self)
        else:
            log.warn(u"Format %s unkown. You've been warned!\n" % _format)
            return _format.upper() + unicode(self)

    def __repr__(self):
        u""" Returns hex value of object

            :return: Hex string of instance's data
            :rtype: hex string
        """
        return self._hex

    def __str__(self):
        u""" Return graphene-base58CheckEncoded string of data

            :return: Base58 encoded data
            :rtype: str
        """
        return gphBase58CheckEncode(self._hex)

    def __bytes__(self):
        u""" Return raw bytes

            :return: Raw bytes of instance
            :rtype: bytes

        """
        return unhexlify(self._hex)


# https://github.com/tochev/python3-cryptocoins/raw/master/cryptocoins/base58.py
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58decode(base58_str):
    base58_text =str(base58_str).encode("ascii")
    n = 0
    leading_zeroes_count = 0
    for b in base58_text:
        n = n * 58 + BASE58_ALPHABET.find(b)
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 256:
        div, mod = divmod(n, 256)
        res.insert(0, mod)
        n = div
    else:
        res.insert(0, n)
    return hexlify(bytearray(1) * leading_zeroes_count + res).decode(u'ascii')


def base58encode(hexstring):
    byteseq = str(unhexlify(str(hexstring).encode('ascii')))
    n = 0
    leading_zeroes_count = 0
    for c in byteseq:
        n = n * 256 + c
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 58:
        div, mod = divmod(n, 58)
        res.insert(0, BASE58_ALPHABET[mod])
        n = div
    else:
        res.insert(0, BASE58_ALPHABET[n])
    return (BASE58_ALPHABET[0:1] * leading_zeroes_count + res).decode(u'ascii')


def ripemd160(s):
    ripemd160 = hashlib.new(u'ripemd160')
    ripemd160.update(unhexlify(s))
    return ripemd160.digest()


def doublesha256(s):
    return hashlib.sha256(hashlib.sha256(unhexlify(s)).digest()).digest()


def b58encode(v):
    return base58encode(v)


def b58decode(v):
    return base58decode(v)


def base58CheckEncode(version, payload):
    s = (u'%.2x' % version) + payload
    checksum = doublesha256(s)[:4]
    result = s + hexlify(checksum).decode(u'ascii')
    return base58encode(result)


def base58CheckDecode(s):
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode(u'ascii')
    checksum = doublesha256(dec)[:4]
    assert(s[-4:] == checksum)
    return dec[2:]


def gphBase58CheckEncode(s):
    checksum = ripemd160(s)[:4]
    result = s + hexlify(checksum).decode(u'ascii')
    return base58encode(result)


def gphBase58CheckDecode(s):
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode(u'ascii')
    checksum = ripemd160(dec)[:4]
    assert(s[-4:] == checksum)
    return dec
