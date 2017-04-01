from __future__ import absolute_import
import struct
import json
from collections import OrderedDict
from graphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, VoteId, ObjectId,
)
from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.account import PublicKey
from graphenebase.operations import (
    Operation as GrapheneOperation
)
from .operationids import operations

default_prefix = u"STM"

asset_precision = {
    u"STEEM": 3,
    u"VESTS": 6,
    u"SBD": 3,
    u"GOLOS": 3,
    u"GESTS": 6,
    u"GBG": 3
}


class Operation(GrapheneOperation):
    def __init__(self, op):
        super(Operation, self).__init__(op)

    def operations(self):
        return operations

    def getOperationKlass(self):
        return Operation

    def getOperationNameForId(self, i):
        for key in operations:
            if int(operations[key]) is int(i):
                return key
        return u"Unknown Operation ID %d" % i

    def _getklass(self, name):
        module = __import__(u"pistonbase.operations", fromlist=[u"operations"])
        class_ = getattr(module, name)
        return class_

    def __str__(self):
        return json.dumps([
            self.getOperationNameForId(self.opId),
            self.op.json()
        ])


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop(u"prefix", default_prefix)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            # Sort keys (FIXME: ideally, the sorting is part of Public
            # Key and not located here)
            kwargs[u"key_auths"] = sorted(
                kwargs[u"key_auths"],
                key=lambda x: repr(PublicKey(x[0], prefix=prefix)),
                reverse=False,
            )
            kwargs[u"account_auths"] = sorted(
                kwargs[u"account_auths"],
                key=lambda x: x[0],
                reverse=False,
            )

            accountAuths = Map([
                [String(e[0]), Uint16(e[1])]
                for e in kwargs[u"account_auths"]
            ])
            keyAuths = Map([
                [PublicKey(e[0], prefix=prefix), Uint16(e[1])]
                for e in kwargs[u"key_auths"]
            ])
            super(Permission, self).__init__(OrderedDict([
                (u'weight_threshold', Uint32(int(kwargs[u"weight_threshold"]))),
                (u'account_auths', accountAuths),
                (u'key_auths', keyAuths),
            ]))


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop(u"prefix", default_prefix)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(Memo, self).__init__(OrderedDict([
                (u'from', PublicKey(kwargs[u"from"], prefix=prefix)),
                (u'to', PublicKey(kwargs[u"to"], prefix=prefix)),
                (u'nonce', Uint64(int(kwargs[u"nonce"]))),
                (u'check', Uint32(int(kwargs[u"check"]))),
                (u'encrypted', Bytes(kwargs[u"encrypted"])),
            ]))


class Vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Vote, self).__init__(OrderedDict([
                (u'voter', String(kwargs[u"voter"])),
                (u'author', String(kwargs[u"author"])),
                (u'permlink', String(kwargs[u"permlink"])),
                (u'weight', Int16(kwargs[u"weight"])),
            ]))


class Comment(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            meta = u""
            if u"json_metadata" in kwargs and kwargs[u"json_metadata"]:
                if (isinstance(kwargs[u"json_metadata"], dict) or
                        isinstance(kwargs[u"json_metadata"], list)):
                    meta = json.dumps(kwargs[u"json_metadata"])
                else:
                    meta = kwargs[u"json_metadata"]

            super(Comment, self).__init__(OrderedDict([
                (u'parent_author', String(kwargs[u"parent_author"])),
                (u'parent_permlink', String(kwargs[u"parent_permlink"])),
                (u'author', String(kwargs[u"author"])),
                (u'permlink', String(kwargs[u"permlink"])),
                (u'title', String(kwargs[u"title"])),
                (u'body', String(kwargs[u"body"])),
                (u'json_metadata', String(meta)),
            ]))


class Amount(object):
    def __init__(self, d):
        self.amount, self.asset = d.strip().split(u" ")
        self.amount = float(self.amount)

        if self.asset in asset_precision:
            self.precision = asset_precision[self.asset]
        else:
            raise Exception(u"Asset unknown")

    def __bytes__(self):
        # padding
        asset = self.asset + u"\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10 ** self.precision)
        return (
            struct.pack(u"<q", amount) +
            struct.pack(u"<b", self.precision) +str(asset).encode("ascii")
        )

    def __str__(self):
        return u'{:.{}f} {}'.format(
            self.amount,
            self.precision,
            self.asset
        )


class Exchange_rate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(Exchange_rate, self).__init__(OrderedDict([
                (u'base', Amount(kwargs[u"base"])),
                (u'quote', Amount(kwargs[u"quote"])),
            ]))


class Witness_props(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(Witness_props, self).__init__(OrderedDict([
                (u'account_creation_fee', Amount(kwargs[u"account_creation_fee"])),
                (u'maximum_block_size', Uint32(kwargs[u"maximum_block_size"])),
                (u'sbd_interest_rate', Uint16(kwargs[u"sbd_interest_rate"])),
            ]))


########################################################
# Actual Operations
########################################################


class Account_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop(u"prefix", default_prefix)

            assert len(kwargs[u"new_account_name"]) <= 16, u"Account name must be at most 16 chars long"

            meta = u""
            if u"json_metadata" in kwargs and kwargs[u"json_metadata"]:
                if isinstance(kwargs[u"json_metadata"], dict):
                    meta = json.dumps(kwargs[u"json_metadata"])
                else:
                    meta = kwargs[u"json_metadata"]
            super(Account_create, self).__init__(OrderedDict([
                (u'fee', Amount(kwargs[u"fee"])),
                (u'creator', String(kwargs[u"creator"])),
                (u'new_account_name', String(kwargs[u"new_account_name"])),
                (u'owner', Permission(kwargs[u"owner"], prefix=prefix)),
                (u'active', Permission(kwargs[u"active"], prefix=prefix)),
                (u'posting', Permission(kwargs[u"posting"], prefix=prefix)),
                (u'memo_key', PublicKey(kwargs[u"memo_key"], prefix=prefix)),
                (u'json_metadata', String(meta)),
            ]))


class Account_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop(u"prefix", default_prefix)

            meta = u""
            if u"json_metadata" in kwargs and kwargs[u"json_metadata"]:
                if isinstance(kwargs[u"json_metadata"], dict):
                    meta = json.dumps(kwargs[u"json_metadata"])
                else:
                    meta = kwargs[u"json_metadata"]

            owner = Permission(kwargs[u"owner"], prefix=prefix) if u"owner" in kwargs else None
            active = Permission(kwargs[u"active"], prefix=prefix) if u"active" in kwargs else None
            posting = Permission(kwargs[u"posting"], prefix=prefix) if u"posting" in kwargs else None

            super(Account_update, self).__init__(OrderedDict([
                (u'account', String(kwargs[u"account"])),
                (u'owner', Optional(owner)),
                (u'active', Optional(active)),
                (u'posting', Optional(posting)),
                (u'memo_key', PublicKey(kwargs[u"memo_key"], prefix=prefix)),
                (u'json_metadata', String(meta)),
            ]))


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if u"memo" not in kwargs:
                kwargs[u"memo"] = u""
            super(Transfer, self).__init__(OrderedDict([
                (u'from', String(kwargs[u"from"])),
                (u'to', String(kwargs[u"to"])),
                (u'amount', Amount(kwargs[u"amount"])),
                (u'memo', String(kwargs[u"memo"])),
            ]))


class Transfer_to_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Transfer_to_vesting, self).__init__(OrderedDict([
                (u'from', String(kwargs[u"from"])),
                (u'to', String(kwargs[u"to"])),
                (u'amount', Amount(kwargs[u"amount"])),
            ]))


class Withdraw_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Withdraw_vesting, self).__init__(OrderedDict([
                (u'account', String(kwargs[u"account"])),
                (u'vesting_shares', Amount(kwargs[u"vesting_shares"])),
            ]))


class Limit_order_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Limit_order_create, self).__init__(OrderedDict([
                (u'owner', String(kwargs[u"owner"])),
                (u'orderid', Uint32(int(kwargs[u"orderid"]))),
                (u'amount_to_sell', Amount(kwargs[u"amount_to_sell"])),
                (u'min_to_receive', Amount(kwargs[u"min_to_receive"])),
                (u'fill_or_kill', Bool(kwargs[u"fill_or_kill"])),
                (u'expiration', PointInTime(kwargs[u"expiration"])),
            ]))


class Limit_order_cancel(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Limit_order_cancel, self).__init__(OrderedDict([
                (u'owner', String(kwargs[u"owner"])),
                (u'orderid', Uint32(int(kwargs[u"orderid"]))),
            ]))


class Set_withdraw_vesting_route(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Set_withdraw_vesting_route, self).__init__(OrderedDict([
                (u'from_account', String(kwargs[u"from_account"])),
                (u'to_account', String(kwargs[u"to_account"])),
                (u'percent', Uint16((kwargs[u"percent"]))),
                (u'auto_vest', Bool(kwargs[u"auto_vest"])),
            ]))


class Convert(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Convert, self).__init__(OrderedDict([
                (u'owner', String(kwargs[u"owner"])),
                (u'requestid', Uint32(kwargs[u"requestid"])),
                (u'amount', Amount(kwargs[u"amount"])),
            ]))


class Feed_publish(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Feed_publish, self).__init__(OrderedDict([
                (u'publisher', String(kwargs[u"publisher"])),
                (u'exchange_rate', Exchange_rate(kwargs[u"exchange_rate"])),
            ]))


class Witness_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop(u"prefix", default_prefix)

            if not kwargs[u"block_signing_key"]:
                kwargs[u"block_signing_key"] = u"STM1111111111111111111111111111111114T1Anm"
            super(Witness_update, self).__init__(OrderedDict([
                (u'owner', String(kwargs[u"owner"])),
                (u'url', String(kwargs[u"url"])),
                (u'block_signing_key', PublicKey(kwargs[u"block_signing_key"], prefix=prefix)),
                (u'props', Witness_props(kwargs[u"props"])),
                (u'fee', Amount(kwargs[u"fee"])),
            ]))


class Transfer_to_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if u"memo" not in kwargs:
                kwargs[u"memo"] = u""
            super(Transfer_to_savings, self).__init__(OrderedDict([
                (u'from', String(kwargs[u"from"])),
                (u'to', String(kwargs[u"to"])),
                (u'amount', Amount(kwargs[u"amount"])),
                (u'memo', String(kwargs[u"memo"])),
            ]))


class Transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if u"memo" not in kwargs:
                kwargs[u"memo"] = u""

            super(Transfer_from_savings, self).__init__(OrderedDict([
                (u'from', String(kwargs[u"from"])),
                (u'request_id', Uint32(int(kwargs[u"request_id"]))),
                (u'to', String(kwargs[u"to"])),
                (u'amount', Amount(kwargs[u"amount"])),
                (u'memo', String(kwargs[u"memo"])),
            ]))


class Cancel_transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Cancel_transfer_from_savings, self).__init__(OrderedDict([
                (u'from', String(kwargs[u"from"])),
                (u'request_id', Uint32(int(kwargs[u"request_id"]))),
            ]))


class Account_witness_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Account_witness_vote, self).__init__(OrderedDict([
                (u'account', String(kwargs[u"account"])),
                (u'witness', String(kwargs[u"witness"])),
                (u'approve', Bool(bool(kwargs[u"approve"]))),
            ]))


class Custom_json(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if u"json" in kwargs and kwargs[u"json"]:
                if (isinstance(kwargs[u"json"], dict) or
                        isinstance(kwargs[u"json"], list)):
                    js = json.dumps(kwargs[u"json"])
                else:
                    js = kwargs[u"json"]

            if len(kwargs[u"id"]) > 32:
                raise Exception(u"'id' too long")

            super(Custom_json, self).__init__(OrderedDict([
                (u'required_auths',
                    Array([String(o) for o in kwargs[u"required_auths"]])),
                (u'required_posting_auths',
                    Array([String(o) for o in kwargs[u"required_posting_auths"]])),
                (u'id', String(kwargs[u"id"])),
                (u'json', String(js)),
            ]))


class Comment_options(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Comment_options, self).__init__(OrderedDict([
                (u'author', String(kwargs[u"author"])),
                (u'permlink', String(kwargs[u"permlink"])),
                (u'max_accepted_payout', Amount(kwargs[u"max_accepted_payout"])),
                (u'percent_steem_dollars', Uint16(int(kwargs[u"percent_steem_dollars"]))),
                (u'allow_votes', Bool(bool(kwargs[u"allow_votes"]))),
                (u'allow_curation_rewards', Bool(bool(kwargs[u"allow_curation_rewards"]))),
                (u'extensions', Array([])),
            ]))
