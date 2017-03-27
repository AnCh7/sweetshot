from piston.account import Account as PistonAccount
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Account(PistonAccount):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Account, self).__init__(*args, **kwargs)
