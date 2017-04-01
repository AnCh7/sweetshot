from __future__ import absolute_import
import logging

log = logging.getLogger(__name__)
try:
    import pymongo
    from pymongo.errors import ConnectionFailure
except ImportError:
    mongo_error = u"""pysteem does not ship with MongoDB driver by default. Please install it by running:\n
    pip install pymongo
    """
    log.error(mongo_error)


class SteemData(object):
    def __init__(self,
                 db_name=u'SteemData',
                 host=u'steemit:steemit@mongo1.steemdata.com',
                 port=27017):
        try:
            self.mongo_url = u'mongodb://%s:%s/%s' % (host, port, db_name)
            client = pymongo.MongoClient(self.mongo_url)
            self.db = client[db_name]

        except ConnectionFailure, e:
            log.error(u'Can not connect to MongoDB server: %s' % e)
            raise
        else:
            self.load_collections()

    def list_collections(self):
        return self.db.collection_names()

    def load_collections(self):
        for coll in self.list_collections():
            setattr(self, coll, self.db[coll])

    def info(self):
        # todo print detailed info and some stats
        return self.mongo_url


if __name__ == u'__main__':
    s = SteemData()
    print s.info()
