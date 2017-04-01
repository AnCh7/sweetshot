from __future__ import absolute_import
import warnings


class GrapheneWebsocketProtocol(object):
    u""" This class is **deprecated**. The old implementation can by
        found in python-bitshares (still deprecated, but functional)
    """

    def __init__(self, *args, **kwargs):
        raise DeprecationWarning(
            u"[DeprecationWarning] The GrapheneWebsocket is deprecated\n"
            u"or BitShares specific. The old implementation can be\b"
            u"found in\n\n"
            u"    from bitsharesapi.websocketprotocol import BitSharesWebsocketProtocol"
        )
        super(GrapheneWebsocketProtocol, self).__init__(*args, **kwargs)
