import hashlib
from binascii import hexlify, unhexlify
import sys
from .account import PrivateKey
from .base58 import Base58, base58decode
import logging
log = logging.getLogger(__name__)

try:
    from Crypto.Cipher import AES
except ImportError:
    raise ImportError(u"Missing dependency: pycrypto")

SCRYPT_MODULE = None
if not SCRYPT_MODULE:
    try:
        import scrypt
        SCRYPT_MODULE = u"scrypt"
    except ImportError:
        try:
            import pylibscrypt as scrypt
            SCRYPT_MODULE = u"pylibscrypt"
        except ImportError:
            raise ImportError(
                u"Missing dependency: scrypt or pylibscrypt"
            )

log.debug(u"Using scrypt module: %s" % SCRYPT_MODULE)

u""" This class and the methods require python3 """
from __future__ import absolute_import
assert sys.version_info[0] == 3, u"graphenelib requires python3"


class SaltException(Exception):
    pass


def _encrypt_xor(a, b, aes):
    u""" Returns encrypt(a ^ b). """
    a = unhexlify(u'%0.32x' % (int((a), 16) ^ int(hexlify(b), 16)))
    return aes.encrypt(a)


def encrypt(privkey, passphrase):
    u""" BIP0038 non-ec-multiply encryption. Returns BIP0038 encrypted privkey.

    :param privkey: Private key
    :type privkey: Base58
    :param str passphrase: UTF-8 encoded passphrase for encryption
    :return: BIP0038 non-ec-multiply encrypted wif key
    :rtype: Base58

    """
    privkeyhex = repr(privkey)   # hex
    addr = format(privkey.uncompressed.address, u"BTC")
    a =str(addr).encode('ascii')
    salt = hashlib.sha256(hashlib.sha256(a).digest()).digest()[0:4]
    if SCRYPT_MODULE == u"scrypt":
        key = scrypt.hash(passphrase, salt, 16384, 8, 8)
    elif SCRYPT_MODULE == u"pylibscrypt":
        key = scrypt.scrypt(str(passphrase).encode("utf-8"), salt, 16384, 8, 8)
    else:
        raise ValueError(u"No scrypt module loaded")
    (derived_half1, derived_half2) = (key[:32], key[32:])
    aes = AES.new(derived_half2)
    encrypted_half1 = _encrypt_xor(privkeyhex[:32], derived_half1[:16], aes)
    encrypted_half2 = _encrypt_xor(privkeyhex[32:], derived_half1[16:], aes)
    u" flag byte is forced 0xc0 because Graphene only uses compressed keys "
    payload = ('\x01' + '\x42' + '\xc0' +
               salt + encrypted_half1 + encrypted_half2)
    u" Checksum "
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    privatkey = hexlify(payload + checksum).decode(u'ascii')
    return Base58(privatkey)


def decrypt(encrypted_privkey, passphrase):
    u"""BIP0038 non-ec-multiply decryption. Returns WIF privkey.

    :param Base58 encrypted_privkey: Private key
    :param str passphrase: UTF-8 encoded passphrase for decryption
    :return: BIP0038 non-ec-multiply decrypted key
    :rtype: Base58
    :raises SaltException: if checksum verification failed (e.g. wrong password)

    """

    d = unhexlify(base58decode(encrypted_privkey))
    d = d[2:]   # remove trailing 0x01 and 0x42
    flagbyte = d[0:1]  # get flag byte
    d = d[1:]   # get payload
    assert flagbyte == '\xc0', u"Flagbyte has to be 0xc0"
    salt = d[0:4]
    d = d[4:-4]
    if SCRYPT_MODULE == u"scrypt":
        key = scrypt.hash(passphrase, salt, 16384, 8, 8)
    elif SCRYPT_MODULE == u"pylibscrypt":
        key = scrypt.scrypt(str(passphrase).encode("utf-8"), salt, 16384, 8, 8)
    else:
        raise ValueError(u"No scrypt module loaded")
    derivedhalf1 = key[0:32]
    derivedhalf2 = key[32:64]
    encryptedhalf1 = d[0:16]
    encryptedhalf2 = d[16:32]
    aes = AES.new(derivedhalf2)
    decryptedhalf2 = aes.decrypt(encryptedhalf2)
    decryptedhalf1 = aes.decrypt(encryptedhalf1)
    privraw = decryptedhalf1 + decryptedhalf2
    privraw = (u'%064x' % (int(hexlify(privraw), 16) ^
                          int(hexlify(derivedhalf1), 16)))
    wif = Base58(privraw)
    u""" Verify Salt """
    privkey = PrivateKey(format(wif, u"wif"))
    addr = format(privkey.uncompressed.address, u"BTC")
    a =str(addr).encode('ascii')
    saltverify = hashlib.sha256(hashlib.sha256(a).digest()).digest()[0:4]
    if saltverify != salt:
        raise SaltException(u'checksum verification failed! Password may be incorrect.')
    return wif
