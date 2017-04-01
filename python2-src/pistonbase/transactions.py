from collections import OrderedDict
from binascii import hexlify, unhexlify
from calendar import timegm
from datetime import datetime
import json
import struct
import time

from pistonbase.account import PublicKey
from .signedtransactions import Signed_Transaction as GrapheneSigned_Transaction

# Import all operations so they can be loaded from this module
from .operations import (
    Operation, Permission, Memo, Vote, Comment, Amount,
    Exchange_rate, Witness_props, Account_create, Account_update,
    Transfer, Transfer_to_vesting, Withdraw_vesting, Limit_order_create,
    Limit_order_cancel, Set_withdraw_vesting_route, Convert, Feed_publish,
    Witness_update, Transfer_to_savings, Transfer_from_savings,
    Cancel_transfer_from_savings, Account_witness_vote, Custom_json,
)
from .chains import known_chains

timeformat = u'%Y-%m-%dT%H:%M:%S%Z'

chain = u"STEEM"
# chain = "TEST"


class Signed_Transaction(GrapheneSigned_Transaction):
    u""" Overwrite default chain:
    """
    def __init__(self, *args, **kwargs):
        super(Signed_Transaction, self).__init__(*args, **kwargs)

    def sign(self, wifkeys, chain=chain):
        return super(Signed_Transaction, self).sign(wifkeys, chain)

    def verify(self, pubkey, chain=chain):
        return super(Signed_Transaction, self).verify(pubkey, chain)


u"""
    Auxiliary Calls
"""


from __future__ import absolute_import
def getBlockParams(ws):
    u""" Auxiliary method to obtain ``ref_block_num`` and
        ``ref_block_prefix``. Requires a websocket connection to a
        witness node!
    """
    dynBCParams = ws.get_dynamic_global_properties()
    ref_block_num = dynBCParams[u"head_block_number"] & 0xFFFF
    ref_block_prefix = struct.unpack_from(u"<I", unhexlify(dynBCParams[u"head_block_id"]), 4)[0]
    return ref_block_num, ref_block_prefix


def formatTimeFromNow(secs=0):
    u""" Properly Format Time that is `x` seconds in the future

     :param int secs: Seconds to go in the future (`x>0`) or the past (`x<0`)
     :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
     :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime(timeformat)
