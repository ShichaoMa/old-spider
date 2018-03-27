#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import json
import pymongo

from toolkit.managers import ExceptContext
from toolkit import load_function as load_class


class MongoItemExporter(load_class("components.ItemExporter")):
    """
        将item存入mongodb
    """
    name = "mongo_item_exporter"

    def __init__(self, **kwargs):
        super(MongoItemExporter, self).__init__(**kwargs)
        self.mongodb_conn = None
        with ExceptContext(Exception, errback=lambda *args: self.stop()):
            self.mongodb_conn = pymongo.MongoClient(
                self.settings.get("MONGODB_SERVER"), self.settings.get_int("MONGODB_PORT"))
            self.mongodb_db = self.mongodb_conn[self.settings.get("MONGODB_DB")]

    def export(self, message):
        with ExceptContext(Exception, errback=self.log_err):
            item = json.loads(message)
            collection = self.mongodb_db[item['collection_name']]
            collection.insert(item, check_keys=False)
            self.logger.info("Insert item into mongoDB collection:%s crawlid: %s, product_id :%s seccessful" % \
                              (item['collection_name'], item.get("crawlid", "unknow"), item.get("product_id")))

    def stop(self, *args):
        super(MongoItemExporter, self).stop(*args)
        with ExceptContext(Exception, errback=lambda *kwargs: True):
            if self.mongodb_conn:
                self.mongodb_conn.close()


if __name__ == "__main__":
    MongoItemExporter().start()
