from piston.witness import Witness as PistonWitness
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Witness(PistonWitness):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Witness, self).__init__(*args, **kwargs)
