# -*- coding:utf-8 -*-
import json
import time
import datetime

from influxdb import InfluxDBClient
from abc import ABCMeta, abstractmethod

from toolkit.monitors import ItemConsumer, ItemProducer
from toolkit.managers import ExceptContext


class ItemExporter(ItemConsumer):
    """
        Export base.
    """
    name = "item_exporter"

    def start(self):
        while self.alive:
            with ExceptContext(Exception, errback=self.log_err):
                message = self.consume()
                if message is None:
                    self.logger.debug("Haven't got message. ")
                    time.sleep(2)
                    continue
                self.logger.debug("Export message. ")
                self.export(message)

    @abstractmethod
    def export(self, message):
        pass


class ItemFilter(ItemConsumer, ItemProducer):
    """
        Filter base.
    """
    name = "item_filter"

    def __init__(self):
        super(ItemFilter, self).__init__()
        self.client = InfluxDBClient(
            self.settings.get("INFLUXDB_HOST", '192.168.200.131'),
            self.settings.get("INFLUXDB_POST", 8086),
            self.settings.get("INFLUXDB_USERNAME", ""),
            self.settings.get("INFLUXDB _PASSWORD", ""),
            self.settings.get("INFLUXDB_DB", 'db_roc')
                                     )

    def start(self):
        while self.alive or [process for process in self.children if process.is_alive()]:
            with ExceptContext(errback=self.log_err):
                message = self.hook()
                if not message:
                    self.logger.debug("Haven't got hook message. ")
                    message = self.consume() if self.alive else None
                    if not message:
                        time.sleep(2)
                        continue
                    else:
                        self.logger.debug("Process message. ")
                        message = self.process_message(message)
                if not message:
                    self.logger.debug("Ignore produce message. ")
                    continue
                self.produce(message)

    def hook(self):
        pass

    def produce(self, message):
        item = json.loads(message)
        self.logger.debug("Start to produce. product_id: %s"%item.get("product_id"))
        super(ItemFilter, self).produce(message)
        site = (item.get("meta", {}).get("tags") or {}).get("source_site_code")
        if site:
            self.client.write_points([{
                "measurement": self.settings.get("MESUREMENT", "roc_ingestion"),
                "tags": {"app": self.__class__.__name__,
                         "item_type": "item", "crawl_type": item.get("meta", {}).get("type"), "site": site},
                "time": datetime.datetime.utcnow(),
                "fields": {"crawlid": item["crawlid"], "value": 1, "etc": ""}
            }])
        self.logger.debug("Produce finished. product_id: %s"%item.get("product_id"))

    def consume(self):
        self.logger.debug("Start to consume. ")
        result = super(ItemFilter, self).consume()
        if result:
            item = json.loads(result)
            site = (item.get("meta", {}).get("tags") or {}).get("source_site_code")
            if site:
                self.client.write_points([{
                    "measurement": self.settings.get("MESUREMENT", "roc_ingestion"),
                    "tags": {"app": self.__class__.__name__,
                             "item_type": "item", "crawl_type": item.get("meta", {}).get("type"), "site": site},
                    "time": datetime.datetime.utcnow(),
                    "fields": {"crawlid": item["crawlid"], "value": -1, "etc": ""}
                }])
            self.logger.debug("Consume finished. product_id: %s" % item.get("product_id"))
        return result

    @abstractmethod
    def process_message(self, message):
        pass
