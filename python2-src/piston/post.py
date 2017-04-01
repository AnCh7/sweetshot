from __future__ import division
from __future__ import absolute_import
import json
import re
from datetime import datetime

from funcy import walk_values
from piston.instance import shared_steem_instance
from pistonbase.operations import Comment_options

from .amount import Amount
from .exceptions import (
    PostDoesNotExist,
    VotingInvalidOnArchivedPost
)
from .utils import (
    resolveIdentifier,
    constructIdentifier,
    remove_from_dict,
    parse_time,
)


class Post(dict):
    u""" This object gets instanciated by Steem.streams and is used as an
        abstraction layer for Comments in Steem

        :param identifier post: The post as obtained by `get_content` or the identifier string of the post (``@author/permlink``)
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    steem = None

    def __init__(
        self,
        post,
        steem_instance=None,
        lazy=False
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.loaded = False

        if isinstance(post, unicode):  # From identifier
            parts = post.split(u"@")
            self.identifier = u"@" + parts[-1]

            if not lazy:
                self.refresh()

        elif (isinstance(post, dict) and  # From dictionary
                u"author" in post and
                u"permlink" in post):
            # strip leading @
            if post[u"author"][0] == u"@":
                post[u"author"] = post[u"author"][1:]
            self.identifier = constructIdentifier(
                post[u"author"],
                post[u"permlink"]
            )

            if u"created" in post:
                self._store_post(post)

        else:
            raise ValueError(u"Post expects an identifier or a dict "
                             u"with author and permlink!")

    def refresh(self):
        post_author, post_permlink = resolveIdentifier(self.identifier)
        post = self.steem.rpc.get_content(post_author, post_permlink)
        if not post[u"permlink"]:
            raise PostDoesNotExist(u"Post does not exist: %s" % self.identifier)

        # If this 'post' comes from an operation, it might carry a patch
        if u"body" in post and re.match(u"^@@", post[u"body"]):
            self._patched = True
            self._patch = post[u"body"]

        # Parse Times
        parse_times = [u"active",
                       u"cashout_time",
                       u"created",
                       u"last_payout",
                       u"last_update",
                       u"max_cashout_time"]
        for p in parse_times:
            post[p] = parse_time(post.get(p, u"1970-01-01T00:00:00"))

        # Parse Amounts
        sbd_amounts = [
            u"total_payout_value",
            u"max_accepted_payout",
            u"pending_payout_value",
            u"curator_payout_value",
            u"total_pending_payout_value",
            u"promoted",
        ]
        for p in sbd_amounts:
            post[p] = Amount(post.get(p, u"0.000 %s" % self.steem.symbol(u"SBD")))

        # Try to properly format json meta data

        try:
            meta_str = post.get(u"json_metadata", u"{}")
            post[u'json_metadata'] = json.loads(meta_str)
        except:
            post[u'json_metadata'] = dict()
        if not post[u'json_metadata'] or post[u"json_metadata"] == u'""':
            post[u'json_metadata'] = dict()

        post[u"tags"] = []
        if post[u"depth"] == 0:
            post[u"tags"] = (
                [post[u"parent_permlink"]] +
                post[u"json_metadata"].get(u"tags", [])
            )

        # Retrieve the root comment
        self.openingPostIdentifier, self.category = self._getOpeningPost(post)

        self._store_post(post)

    def _store_post(self, post):
        # Store original values as obtained from the rpc
        for key, value in post.items():
            super(Post, self).__setitem__(key, value)

        # Set attributes as well
        for key in post:
            setattr(self, key, post[key])

        # also set identifier
        super(Post, self).__setitem__(u"identifier", self.identifier)

        self.loaded = True

    def __getattr__(self, key):
        if not self.loaded:
            self.refresh()
        return object.__getattribute__(self, key)

    def __getitem__(self, key):
        if not self.loaded:
            self.refresh()
        return super(Post, self).__getitem__(key)

    def __repr__(self):
        return u"<Post-%s>" % self.identifier

    __str__ = __repr__

    def _getOpeningPost(self, post=None):
        if not post:
            post = self
        m = re.match(u"/([^/]*)/@([^/]*)/([^#]*).*",
                     post.get(u"url", u""))
        if not m:
            return u"", u""
        else:
            category = m.group(1)
            author = m.group(2)
            permlink = m.group(3)
            return constructIdentifier(
                author, permlink
            ), category

    def get_comments(self, sort=u"total_payout_value"):
        u""" Return **first-level** comments of the post.
        """
        post_author, post_permlink = resolveIdentifier(self.identifier)
        posts = self.steem.rpc.get_content_replies(post_author, post_permlink)
        r = []
        for post in posts:
            r.append(Post(post, steem_instance=self.steem))
        if sort == u"total_payout_value":
            r = sorted(r, key=lambda x: float(
                x[u"total_payout_value"]
            ), reverse=True)
        elif sort == u"total_payout_value":
            r = sorted(r, key=lambda x: float(
                x[u"total_payout_value"]
            ), reverse=True)
        else:
            r = sorted(r, key=lambda x: x[sort])
        return(r)

    def reply(self, body, title=u"", author=u"", meta=None):
        u""" Reply to the post

            :param str body: (required) body of the reply
            :param str title: Title of the reply
            :param str author: Author of reply
            :param json meta: JSON Meta data
        """
        return self.steem.reply(self.identifier, body, title, author, meta)

    def upvote(self, weight=+100, voter=None):
        u""" Upvote the post

            :param float weight: (optional) Weight for posting (-100.0 - +100.0) defaults to +100.0
            :param str voter: (optional) Voting account
        """
        return self.vote(weight, voter=voter)

    def downvote(self, weight=-100, voter=None):
        u""" Downvote the post

            :param float weight: (optional) Weight for posting (-100.0 - +100.0) defaults to -100.0
            :param str voter: (optional) Voting account
        """
        return self.vote(weight, voter=voter)

    def vote(self, weight, voter=None):
        u""" Vote the post

            :param float weight: Weight for posting (-100.0 - +100.0)
            :param str voter: Voting account
        """
        return self.steem.vote(self.identifier, weight, voter=voter)

    @property
    def reward(self):
        u"""Return a float value of estimated total SBD reward.
        """
        if not self.loaded:
            self.refresh()
        return self[u'total_payout_value']

    @property
    def meta(self):
        if not self.loaded:
            self.refresh()
        return self.get(u'json_metadata', dict())

    def time_elapsed(self):
        u"""Return a timedelta on how old the post is.
        """
        return datetime.utcnow() - self[u'created']

    def is_main_post(self):
        u""" Retuns True if main post, and False if this is a comment (reply).
        """
        return self[u'depth'] == 0

    def is_opening_post(self):
        u""" Retuns True if main post, and False if this is a comment (reply).
        """
        return self[u'depth'] == 0

    def is_comment(self):
        u""" Retuns True if post is a comment
        """
        return self[u'depth'] > 0

    def curation_reward_pct(self):
        u""" If post is less than 30 minutes old, it will incur a curation reward penalty.
        """
        reward = (self.time_elapsed().seconds / 1800) * 100
        if reward > 100:
            reward = 100
        return reward

    def export(self):
        u""" This method returns a dictionary that is type-safe to store as JSON or in a database.
        """
        self.refresh()

        # Remove Steem instance object
        safe_dict = remove_from_dict(self, [u'steem'])

        # Convert Amount class objects into pure dictionaries
        def decompose_amounts(item):
            if type(item) == Amount:
                return item.__dict__
            return item
        return walk_values(decompose_amounts, safe_dict)

    def set_comment_options(self, options):
        op = Comment_options(
            **{u"author": self[u"author"],
               u"permlink": self[u"permlink"],
               u"max_accepted_payout":
                   options.get(u"max_accepted_payout", unicode(self[u"max_accepted_payout"])),
               u"percent_steem_dollars": int(
                   options.get(u"percent_steem_dollars",
                               self[u"percent_steem_dollars"] / 100
                               ) * 100),
               u"allow_votes":
                   options.get(u"allow_votes", self[u"allow_votes"]),
               u"allow_curation_rewards":
                   options.get(u"allow_curation_rewards", self[u"allow_curation_rewards"]),
               }
        )
        return self.steem.finalizeOp(op, self[u"author"], u"posting")
