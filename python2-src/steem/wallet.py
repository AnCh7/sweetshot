from __future__ import absolute_import
from piston.wallet import Wallet as PistonWallet
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Wallet(PistonWallet):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Wallet, self).__init__(*args, **kwargs)
