from piston.blockchain import Blockchain as PistonBlockchain
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Blockchain(PistonBlockchain):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Blockchain, self).__init__(*args, **kwargs)
