from __future__ import absolute_import
import re
from grapheneapi.graphenewsrpc import RPCError


def decodeRPCErrorMsg(e):
    u""" Helper function to decode the raised Exception and give it a
        python Exception class
    """
    found = re.search(
        (
            u"(10 assert_exception: Assert Exception\n|"
            u"3030000 tx_missing_posting_auth)"
            u".*: (.*)\n"
        ),
        unicode(e),
        flags=re.M)
    if found:
        return found.group(2).strip()
    else:
        return unicode(e)


class NoAccessApi(RPCError):
    pass


class AlreadyTransactedThisBlock(RPCError):
    pass


class VoteWeightTooSmall(RPCError):
    pass


class OnlyVoteOnceEvery3Seconds(RPCError):
    pass


class AlreadyVotedSimilarily(RPCError):
    pass


class NoMethodWithName(RPCError):
    pass


class PostOnlyEvery5Min(RPCError):
    pass


class DuplicateTransaction(RPCError):
    pass


class MissingRequiredPostingAuthority(RPCError):
    pass


class UnhandledRPCError(RPCError):
    pass


class ExceededAllowedBandwidth(RPCError):
    pass
