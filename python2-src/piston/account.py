from __future__ import division
from __future__ import with_statement
from __future__ import absolute_import
import datetime
import json
import math
import time
from contextlib import suppress

from piston.instance import shared_steem_instance

from .amount import Amount
from .converter import Converter
from .exceptions import AccountDoesNotExistsException
from .utils import parse_time


class Account(dict):
    u""" This class allows to easily access Account data

        :param str account_name: Name of the account
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    def __init__(
        self,
        account_name,
        steem_instance=None,
        lazy=False,
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.cached = False
        self.name = account_name

        # caches
        self._converter = None

        if not lazy:
            self.refresh()

    def refresh(self):
        account = self.steem.rpc.get_account(self.name)
        if not account:
            raise AccountDoesNotExistsException
        super(Account, self).__init__(account)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Account, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return super(Account, self).items()

    @property
    def converter(self):
        if not self._converter:
            self._converter = Converter(self.steem)
        return self._converter

    @property
    def profile(self):
        with suppress(Exception):
            meta_str = self.get(u"json_metadata", u"")
            return json.loads(meta_str).get(u'profile', dict())

    @property
    def sp(self):
        vests = Amount(self[u'vesting_shares']).amount
        return round(self.converter.vests_to_sp(vests), 3)

    @property
    def rep(self):
        return self.reputation()

    @property
    def balances(self):
        return self.get_balances()

    def get_balances(self, as_float=False):
        my_account_balances = self.steem.get_balances(self.name)
        balance = {
            u"STEEM": my_account_balances[u"balance"],
            u"SBD": my_account_balances[u"sbd_balance"],
            u"VESTS": my_account_balances[u"vesting_shares"],
            u"SAVINGS_STEEM": my_account_balances[u"savings_balance"],
            u"SAVINGS_SBD": my_account_balances[u"savings_sbd_balance"]
        }
        if as_float:
            return dict((k, v.amount) for k, v in balance.items())
        else:
            return balance

    def reputation(self, precision=2):
        rep = int(self[u'reputation'])
        if rep == 0:
            return 25
        score = (math.log10(abs(rep)) - 9) * 9 + 25
        if rep < 0:
            score = 50 - score
        return round(score, precision)

    def voting_power(self):
        return self[u'voting_power'] / 100

    def get_followers(self):
        return [x[u'follower'] for x in self._get_followers(direction=u"follower")]

    def get_following(self):
        return [x[u'following'] for x in self._get_followers(direction=u"following")]

    def _get_followers(self, direction=u"follower", last_user=u""):
        if direction == u"follower":
            followers = self.steem.rpc.get_followers(self.name, last_user, u"blog", 100, api=u"follow")
        elif direction == u"following":
            followers = self.steem.rpc.get_following(self.name, last_user, u"blog", 100, api=u"follow")
        if len(followers) >= 100:
            followers += self._get_followers(direction=direction, last_user=followers[-1][direction])[1:]
        return followers

    def has_voted(self, post):
        active_votes = dict((v[u"voter"], v) for v in getattr(post, u"active_votes"))
        return self.name in active_votes

    def curation_stats(self):
        trailing_24hr_t = time.time() - datetime.timedelta(hours=24).total_seconds()
        trailing_7d_t = time.time() - datetime.timedelta(days=7).total_seconds()

        reward_24h = 0.0
        reward_7d = 0.0

        for reward in self.history2(filter_by=u"curation_reward", take=10000):

            timestamp = parse_time(reward[u'timestamp']).timestamp()
            if timestamp > trailing_7d_t:
                reward_7d += Amount(reward[u'reward']).amount

            if timestamp > trailing_24hr_t:
                reward_24h += Amount(reward[u'reward']).amount

        reward_7d = self.converter.vests_to_sp(reward_7d)
        reward_24h = self.converter.vests_to_sp(reward_24h)
        return {
            u"24hr": reward_24h,
            u"7d": reward_7d,
            u"avg": reward_7d / 7,
        }

    def virtual_op_count(self):
        try:
            last_item = self.steem.rpc.get_account_history(self.name, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def get_account_votes(self):
        return self.steem.rpc.get_account_votes(self.name)

    def get_withdraw_routes(self):
        return self.steem.rpc.get_withdraw_routes(self.name, u'all')

    def get_conversion_requests(self):
        return self.steem.rpc.get_conversion_requests(self.name)

    @staticmethod
    def filter_by_date(items, start_time, end_time=None):
        start_time = parse_time(start_time).timestamp()
        if end_time:
            end_time = parse_time(end_time).timestamp()
        else:
            end_time = time.time()

        filtered_items = []
        for item in items:
            if u'time' in item:
                item_time = item[u'time']
            elif u'timestamp' in item:
                item_time = item[u'timestamp']
            timestamp = parse_time(item_time).timestamp()
            if end_time > timestamp > start_time:
                filtered_items.append(item)

        return filtered_items

    def history(self, filter_by=None, start=0):
        u"""
        Take all elements from start to last from history, oldest first.
        """
        batch_size = 1000
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while True:
            if i == start_index:
                limit = batch_size
            else:
                limit = batch_size - 1
            history = self.steem.rpc.get_account_history(self.name, i, limit)
            for item in history:
                index = item[0]
                if index >= max_index:
                    return

                op_type = item[1][u'op'][0]
                op = item[1][u'op'][1]
                timestamp = item[1][u'timestamp']
                trx_id = item[1][u'trx_id']

                def construct_op(account_name):
                    r = {
                        u"index": index,
                        u"account": account_name,
                        u"trx_id": trx_id,
                        u"timestamp": timestamp,
                        u"type": op_type,
                    }
                    r.update(op)
                    return r

                if filter_by is None:
                    yield construct_op(self.name)
                else:
                    if type(filter_by) is list:
                        if op_type in filter_by:
                            yield construct_op(self.name)

                    if type(filter_by) is unicode:
                        if op_type == filter_by:
                            yield construct_op(self.name)
            i += batch_size

    def history2(self, filter_by=None, take=1000):
        u"""
        Take X elements from most recent history, oldest first.
        """
        max_index = self.virtual_op_count()
        start_index = max_index - take
        if start_index < 0:
            start_index = 0

        return self.history(filter_by, start=start_index)

    def rawhistory(
        self, first=99999999999,
        limit=-1, only_ops=[], exclude_ops=[]
    ):
        u""" Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param str account: account name to get history for
            :param int first: sequence number of the first transaction to return
            :param int limit: limit number of transactions to return
            :param array only_ops: Limit generator by these operations
        """
        cnt = 0
        _limit = 100
        if _limit > first:
            _limit = first
        while first > 0:
            # RPC call
            txs = self.steem.rpc.get_account_history(self.name, first, _limit)
            for i in txs[::-1]:
                if exclude_ops and i[1][u"op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1][u"op"][0] in only_ops:
                    cnt += 1
                    yield i
                    if limit >= 0 and cnt >= limit:
                        break
            if limit >= 0 and cnt >= limit:
                break
            if len(txs) < _limit:
                break
            first = txs[0][0] - 1  # new first
            if _limit > first:
                _limit = first
