from piston.blog import Blog as PistonBlog
import warnings
warnings.simplefilter('always', DeprecationWarning)


class Blog(PistonBlog):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Please use the API compatible 'piston-lib' in future",
            DeprecationWarning
        )
        super(Blog, self).__init__(*args, **kwargs)
