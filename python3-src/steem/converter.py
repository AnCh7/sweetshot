from piston.converter import Converter as PistonConverter
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Converter(PistonConverter):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Converter, self).__init__(*args, **kwargs)
