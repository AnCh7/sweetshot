from __future__ import absolute_import
from piston.witness import Witness as PistonWitness
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Witness(PistonWitness):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Witness, self).__init__(*args, **kwargs)
