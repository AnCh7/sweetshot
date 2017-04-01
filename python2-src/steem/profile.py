from __future__ import absolute_import
from piston.profile import Profile as PistonProfile
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Profile(PistonProfile):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Profile, self).__init__(*args, **kwargs)
