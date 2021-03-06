from piston.data import SteemData as PistonSteemData
import warnings
warnings.simplefilter('always', DeprecationWarning)


class SteemData(PistonSteemData):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(SteemData, self).__init__(*args, **kwargs)
