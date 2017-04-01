from piston.block import Block as PistonBlock
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Block(PistonBlock):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Block, self).__init__(*args, **kwargs)
