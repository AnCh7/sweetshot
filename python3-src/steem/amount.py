from piston.amount import Amount as PistonAmount
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Amount(PistonAmount):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Amount, self).__init__(*args, **kwargs)
