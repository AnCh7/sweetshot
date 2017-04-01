from __future__ import absolute_import
from piston.transactionbuilder import TransactionBuilder as PistonTransactionBuilder
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class TransactionBuilder(PistonTransactionBuilder):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(TransactionBuilder, self).__init__(*args, **kwargs)
