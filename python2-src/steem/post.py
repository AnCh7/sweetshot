from __future__ import absolute_import
from piston.post import Post as PistonPost
import warnings
warnings.simplefilter(u'always', DeprecationWarning)


class Post(PistonPost):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            u"Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Post, self).__init__(*args, **kwargs)
