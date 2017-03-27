from piston.dex import Dex as PistonDex
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Dex(PistonDex):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Dex, self).__init__(*args, **kwargs)
