import warnings
from .steem import Steem

warnings.simplefilter('always', DeprecationWarning)
warnings.warn(
    """\n
    The python-steem brand has been overtaken by Steemit Inc. and is no
    longer available for our python development! You can find the
    rebranded library as 'piston-lib' and can use it by simply replacing
          from steem.X import Y
    by
          from piston.X import Y""",
    DeprecationWarning
)

__all__ = [
    "aes",
    "amount",
    "post",
    "profile",
    "steem",
    "storage",
    "wallet",
    "dex",
    "transactions",
    "witness",
    "instance",
    "data",
]
