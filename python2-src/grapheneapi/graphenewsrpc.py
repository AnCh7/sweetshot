from __future__ import absolute_import
import sys
import threading
import websocket
import ssl
import json
import time
from itertools import cycle
import warnings
import logging
log = logging.getLogger(__name__)


class RPCError(Exception):
    pass


class NumRetriesReached(Exception):
    pass


class GrapheneWebsocketRPC(object):
    u""" This class allows to call API methods synchronously, without
        callbacks. It logs in and registers to the APIs:

        * database
        * history

        :param str urls: Either a single Websocket URL, or a list of URLs
        :param str user: Username for Authentication
        :param str password: Password for Authentication
        :param Array apis: List of APIs to register to (default: ["database", "network_broadcast"])
        :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely

        Available APIs

              * database
              * network_node
              * network_broadcast
              * history

        Usage:

        .. code-block:: python

            ws = GrapheneWebsocketRPC("ws://10.0.0.16:8090","","")
            print(ws.get_account_count())

        .. note:: This class allows to call methods available via
                  websocket. If you want to use the notification
                  subsystem, please use ``GrapheneWebsocket`` instead.

    """
    def __init__(self, urls, user=u"", password=u"", **kwargs):
        self.api_id = {}
        self._request_id = 0
        if isinstance(urls, list):
            self.urls = cycle(urls)
        else:
            self.urls = cycle([urls])
        self.user = user
        self.password = password
        self.num_retries = kwargs.get(u"num_retries", -1)

        self.wsconnect()
        self.register_apis()

    def get_request_id(self):
        self._request_id += 1
        return self._request_id

    def wsconnect(self):
        cnt = 0
        while True:
            cnt += 1
            self.url = self.urls.next()
            log.debug(u"Trying to connect to node %s" % self.url)
            if self.url[:3] == u"wss":
                sslopt_ca_certs = {u'cert_reqs': ssl.CERT_NONE}
                self.ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
            else:
                self.ws = websocket.WebSocket()
            try:
                self.ws.connect(self.url)
                break
            except KeyboardInterrupt:
                raise
            except:
                if (self.num_retries >= 0 and cnt > self.num_retries):
                    raise NumRetriesReached()

                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.warning(
                        u"Lost connection to node during wsconnect(): %s (%d/%d) "
                        % (self.url, cnt, self.num_retries) +
                        u"Retrying in %d seconds" % sleeptime
                    )
                    time.sleep(sleeptime)
        self.login(self.user, self.password, api_id=1)

    def register_apis(self):
        self.api_id[u"database"] = self.database(api_id=1)
        self.api_id[u"history"] = self.history(api_id=1)
        self.api_id[u"network_broadcast"] = self.network_broadcast(api_id=1)

    u""" RPC Calls
    """
    def rpcexec(self, payload):
        u""" Execute a call by sending the payload

            :param json payload: Payload data
            :raises ValueError: if the server does not respond in proper JSON format
            :raises RPCError: if the server returns an error
        """
        log.debug(json.dumps(payload))
        cnt = 0
        while True:
            cnt += 1

            try:
                self.ws.send(json.dumps(payload, ensure_ascii=False).encode(u'utf8'))
                reply = self.ws.recv()
                break
            except KeyboardInterrupt:
                raise
            except:
                if (self.num_retries > -1 and
                        cnt > self.num_retries):
                    raise NumRetriesReached()
                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.warning(
                        u"Lost connection to node during rpcexec(): %s (%d/%d) "
                        % (self.url, cnt, self.num_retries) +
                        u"Retrying in %d seconds" % sleeptime
                    )
                    time.sleep(sleeptime)

                # retry
                try:
                    self.ws.close()
                    time.sleep(sleeptime)
                    self.wsconnect()
                    self.register_apis()
                except:
                    pass

        ret = {}
        try:
            ret = json.loads(reply, strict=False)
        except ValueError:
            raise ValueError(u"Client returned invalid format. Expected JSON!")

        log.debug(json.dumps(reply))

        if u'error' in ret:
            if u'detail' in ret[u'error']:
                raise RPCError(ret[u'error'][u'detail'])
            else:
                raise RPCError(ret[u'error'][u'message'])
        else:
            return ret[u"result"]

    # End of Deprecated methods
    ####################################################################
    def __getattr__(self, name):
        u""" Map all methods to RPC calls and pass through the arguments
        """
        def method(*args, **kwargs):

            # Sepcify the api to talk to
            if u"api_id" not in kwargs:
                if (u"api" in kwargs):
                    if (kwargs[u"api"] in self.api_id and
                            self.api_id[kwargs[u"api"]]):
                        api_id = self.api_id[kwargs[u"api"]]
                    else:
                        raise ValueError(
                            u"Unknown API! "
                            u"Verify that you have registered to %s"
                            % kwargs[u"api"]
                        )
                else:
                    api_id = 0
            else:
                api_id = kwargs[u"api_id"]

            # let's be able to define the num_retries per query
            self.num_retries = kwargs.get(u"num_retries", self.num_retries)

            query = {u"method": u"call",
                     u"params": [api_id, name, list(args)],
                     u"jsonrpc": u"2.0",
                     u"id": self.get_request_id()}
            r = self.rpcexec(query)
            return r
        return method