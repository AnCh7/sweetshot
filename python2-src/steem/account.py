from __future__ import absolute_import
from piston.account import Account as PistonAccount
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Account(PistonAccount):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Account, self).__init__(*args, **kwargs)
