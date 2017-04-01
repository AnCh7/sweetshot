import sys
import hashlib
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from steembase.account import PrivateKey, PublicKey
from graphenebase.base58 import base58encode, base58decode
import struct

u" This class and the methods require python3 "
from __future__ import absolute_import
assert sys.version_info[0] == 3, u"graphenelib requires python3"

default_prefix = u"STM"


def get_shared_secret(priv, pub):
    u""" Derive the share secret between ``priv`` and ``pub``

        :param `Base58` priv: Private Key
        :param `Base58` pub: Public Key
        :return: Shared secret
        :rtype: hex

        The shared secret is generated such that::

            Pub(Alice) * Priv(Bob) = Pub(Bob) * Priv(Alice)

    """
    pub_point = pub.point()
    priv_point = int(repr(priv), 16)
    res = pub_point * priv_point
    res_hex = u'%032x' % res.x()
    # Zero padding
    res_hex = u'0' * (64 - len(res_hex)) + res_hex
    return hashlib.sha512(unhexlify(res_hex)).hexdigest()


def init_aes(shared_secret, nonce):
    u""" Initialize AES instance

        :param hex shared_secret: Shared Secret to use as encryption key
        :param int nonce: Random nonce
        :return: AES instance and checksum of the encryption key
        :rtype: length 2 tuple

    """
    u" Seed "
    ss = unhexlify(shared_secret)
    n = struct.pack(u"<Q", int(nonce))
    encryption_key = hashlib.sha512(n + ss).hexdigest()
    u" Check'sum' "
    check = hashlib.sha256(unhexlify(encryption_key)).digest()
    check = struct.unpack_from(u"<I", check[:4])[0]
    u" AES "
    key = unhexlify(encryption_key[0:64])
    iv = unhexlify(encryption_key[64:96])
    return AES.new(key, AES.MODE_CBC, iv), check


def _pad(s, BS):
    numBytes = (BS - len(s) % BS)
    return s + numBytes * struct.pack(u'B', numBytes)


def _unpad(s, BS):
    count = int(struct.unpack(u'B',str(s[-1]).encode('ascii'))[0])
    ifstr(s[-count::]).encode('ascii') == count * struct.pack(u'B', count):
        return s[:-count]
    return s


def encode_memo(priv, pub, nonce, message, **kwargs):
    u""" Encode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Alice)
        :param PublicKey pub: Public Key (of Bob)
        :param int nonce: Random nonce
        :param str message: Memo message
        :return: Encrypted message
        :rtype: hex

    """
    from steembase import transactions
    shared_secret = get_shared_secret(priv, pub)
    aes, check = init_aes(shared_secret, nonce)
    raw =str(message).encode('utf8')
    u" Padding "
    BS = 16
    if len(raw) % BS:
        raw = _pad(raw, BS)
    u" Encryption "
    cipher = hexlify(aes.encrypt(raw)).decode(u'ascii')
    prefix = kwargs.pop(u"prefix", default_prefix)
    s = {
        u"from": format(priv.pubkey, prefix),
        u"to": format(pub, prefix),
        u"nonce": nonce,
        u"check": check,
        u"encrypted": cipher,
        u"from_priv": repr(priv),
        u"to_pub": repr(pub),
        u"shared_secret": shared_secret,
    }
    tx = transactions.Memo(**s)
    return u"#" + base58encode(hexlify(str(tx)).decode(u"ascii"))


def decode_memo(priv, message):
    u""" Decode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Bob)
        :param base58encoded message: Encrypted Memo message
        :return: Decrypted message
        :rtype: str
        :raise ValueError: if message cannot be decoded as valid UTF-8
               string

    """
    u" decode structure "
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])
    raw = raw[66:]
    nonce = unicode(struct.unpack_from(u"<Q", unhexlify(raw[:16]))[0])
    raw = raw[16:]
    check = struct.unpack_from(u"<I", unhexlify(raw[:8]))[0]
    raw = raw[8:]
    cipher = raw

    if repr(to_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, from_key)
    elif repr(from_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, to_key)
    else:
        raise ValueError(u"Incorrect PrivateKey")

    u" Init encryption "
    aes, checksum = init_aes(shared_secret, nonce)

    u" Check "
    assert check == checksum, u"Checksum failure"

    u" Encryption "
    # remove the varint prefix (FIXME, long messages!)
    message = cipher[2:]
    from graphenebase.types import varintdecode
    message = aes.decrypt(unhexlify(str(message).encode('ascii')))
    try:
        return _unpad(message.decode(u'utf8'), 16)
    except:
        raise ValueError(message)


def involved_keys(message):
    u" decode structure "
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])

    return [from_key, to_key]
