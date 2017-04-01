from __future__ import absolute_import
import warnings


class GrapheneClient(object):
    u""" This class is **deprecated**. The old implementation can by
        found in python-bitshares (still deprecated, but functional)
    """

    def __init__(self, *args, **kwargs):
        raise DeprecationWarning(
            u"[DeprecationWarning] The GrapheneClient is deprecated. The "
            u"old implementation can be found in\n\n"
            u"    from bitsharesdeprecated.client import BitSharesClient"
        )
        super(GrapheneClient, self).__init__(*args, **kwargs)
