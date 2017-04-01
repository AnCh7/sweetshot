from __future__ import absolute_import
from piston.blockchain import Blockchain as PistonBlockchain
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Blockchain(PistonBlockchain):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Blockchain, self).__init__(*args, **kwargs)
