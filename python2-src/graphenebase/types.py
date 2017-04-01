from __future__ import absolute_import
from binascii import hexlify, unhexlify
import time
from calendar import timegm
from datetime import datetime
import struct
from collections import OrderedDict
import json

from .objecttypes import object_type

timeformat = u'%Y-%m-%dT%H:%M:%S%Z'


def varint(n):
    u""" Varint encoding
    """
    data = ''
    while n >= 0x80:
        data += str([(n & 0x7f) | 0x80])
        n >>= 7
    data += str([n])
    return data


def varintdecode(data):
    u""" Varint decoding
    """
    shift = 0
    result = 0
    for c in data:
        b = ord(c)
        result |= ((b & 0x7f) << shift)
        if not (b & 0x80):
            break
        shift += 7
    return result


def variable_buffer(s):
    u""" Encode variable length buffer
    """
    return varint(len(s)) + s


def JsonObj(data):
    u""" Returns json object from data
    """
    return json.loads(unicode(data))


class Uint8(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return struct.pack(u"<B", self.data)

    def __str__(self):
        return u'%d' % self.data


class Int16(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack(u"<h", int(self.data))

    def __str__(self):
        return u'%d' % self.data


class Uint16(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack(u"<H", self.data)

    def __str__(self):
        return u'%d' % self.data


class Uint32(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack(u"<I", self.data)

    def __str__(self):
        return u'%d' % self.data


class Uint64(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack(u"<Q", self.data)

    def __str__(self):
        return u'%d' % self.data


class Varint32(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return varint(self.data)

    def __str__(self):
        return u'%d' % self.data


class Int64(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return struct.pack(u"<q", self.data)

    def __str__(self):
        return u'%d' % self.data


class String(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        d = self.unicodify()
        return varint(len(d)) + d

    def __str__(self):
        return u'%s' % unicode(self.data)

    def unicodify(self):
        r = []
        for s in self.data:
            o = ord(s)
            if o <= 7:
                r.append(u"u%04x" % o)
            elif o == 8:
                r.append(u"b")
            elif o == 9:
                r.append(u"\t")
            elif o == 10:
                r.append(u"\n")
            elif o == 11:
                r.append(u"u%04x" % o)
            elif o == 12:
                r.append(u"f")
            elif o == 13:
                r.append(u"\r")
            elif o > 13 and o < 32:
                r.append(u"u%04x" % o)
            else:
                r.append(s)
        returnstr("".join(r)).encode("utf-8")


class Bytes(object):
    def __init__(self, d, length=None):
        self.data = d
        if length:
            self.length = length
        else:
            self.length = len(self.data)

    def __bytes__(self):
        # FIXME constraint data to self.length
        d = unhexlify(str(self.data).encode('utf-8'))
        return varint(len(d)) + d

    def __str__(self):
        return unicode(self.data)


class Void(object):
    def __init__(self):
        pass

    def __bytes__(self):
        return ''

    def __str__(self):
        return u""


class Array(object):
    def __init__(self, d):
        self.data = d
        self.length = Varint32(len(self.data))

    def __bytes__(self):
        return str(self.length) + "".join([str(a) for a in self.data])

    def __str__(self):
        r = []
        for a in self.data:
            if isinstance(a, ObjectId):
                r.append(unicode(a))
            elif isinstance(a, VoteId):
                r.append(unicode(a))
            elif isinstance(a, String):
                r.append(unicode(a))
            else:
                r.append(JsonObj(a))
        return json.dumps(r)


class PointInTime(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return struct.pack(u"<I", timegm(time.strptime((self.data + u"UTC"), timeformat)))

    def __str__(self):
        return self.data


class Signature(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return self.data

    def __str__(self):
        return json.dumps(hexlify(self.data).decode(u'ascii'))


class Bool(Uint8):  # Bool = Uint8
    def __init__(self, d):
        super(Bool, self).__init__(d)

    def __str__(self):
        return True if self.data else False


class Set(Array):  # Set = Array
    def __init__(self, d):
        super(Set, self).__init__(d)


class Fixed_array(object):
    def __init__(self, d):
        raise NotImplementedError

    def __bytes__(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class Optional(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        if not self.data:
            return str(Bool(0))
        else:
            return str(Bool(1)) + str(self.data) if str(self.data) else str(Bool(0))

    def __str__(self):
        return unicode(self.data)

    def isempty(self):
        if not self.data:
            return True
        return not bool(str(self.data))


class Static_variant(object):
    def __init__(self, d, type_id):
        self.data = d
        self.type_id = type_id

    def __bytes__(self):
        return varint(self.type_id) + str(self.data)

    def __str__(self):
        return {self._type_id: unicode(self.data)}


class Map(object):
    def __init__(self, data):
        self.data = data

    def __bytes__(self):
        b = ""
        b += varint(len(self.data))
        for e in self.data:
            b += str(e[0]) + str(e[1])
        return b

    def __str__(self):
        r = []
        for e in self.data:
            r.append([unicode(e[0]), unicode(e[1])])
        return json.dumps(r)


class Id(object):
    def __init__(self, d):
        self.data = Varint32(d)

    def __bytes__(self):
        return str(self.data)

    def __str__(self):
        return unicode(self.data)


class VoteId(object):
    def __init__(self, vote):
        parts = vote.split(u":")
        assert len(parts) == 2
        self.type = int(parts[0])
        self.instance = int(parts[1])

    def __bytes__(self):
        binary = (self.type & 0xff) | (self.instance << 8)
        return struct.pack(u"<I", binary)

    def __str__(self):
        return u"%d:%d" % (self.type, self.instance)


class ObjectId(object):
    u""" Encodes object/protocol ids
    """
    def __init__(self, object_str, type_verify=None):
        if len(object_str.split(u".")) == 3:
            space, type, id = object_str.split(u".")
            self.space = int(space)
            self.type = int(type)
            self.instance = Id(int(id))
            self.Id = object_str
            if type_verify:
                assert object_type[type_verify] == int(type),\
                    u"Object id does not match object type! " +\
                    u"Excpected %d, got %d" %\
                    (object_type[type_verify], int(type))
        else:
            raise Exception(u"Object id is invalid")

    def __bytes__(self):
        return str(self.instance)  # only yield instance

    def __str__(self):
        return self.Id
