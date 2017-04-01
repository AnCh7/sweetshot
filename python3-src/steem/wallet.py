from piston.wallet import Wallet as PistonWallet
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Wallet(PistonWallet):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Wallet, self).__init__(*args, **kwargs)
