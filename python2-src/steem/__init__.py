from __future__ import absolute_import
import warnings
from .steem import Steem

warnings.simplefilter(u'always', DeprecationWarning)
warnings.warn(
    u"""\n
    The python-steem brand has been overtaken by Steemit Inc. and is no
    longer available for our python development! You can find the
    rebranded library as 'piston-lib' and can use it by simply replacing
          from steem.X import Y
    by
          from piston.X import Y""",
    DeprecationWarning
)

__all__ = [
    u"aes",
    u"amount",
    u"post",
    u"profile",
    u"steem",
    u"storage",
    u"wallet",
    u"dex",
    u"transactions",
    u"witness",
    u"instance",
    u"data",
]
