# -*- coding:utf-8 -*-
import json
import datetime
from influxdb import InfluxDBClient
from scrapy.http import Request
from .spiders.utils import Logger


class BaseSpiderMiddleware(object):

    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.logger = Logger.from_crawler(crawler)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)


class ItemProcessMiddleware(BaseSpiderMiddleware):

    def process_spider_output(self, response, result, spider):
        for r in result:
            if not isinstance(r, Request):
                r = self.process_item(r, response, spider)
            yield r

    def process_item(self, item, response, spider):
        pass


class InfluxDBMiddleware(ItemProcessMiddleware):

    def __init__(self, crawler):
        super(InfluxDBMiddleware, self).__init__(crawler)
        self.client = InfluxDBClient(
            crawler.settings.get("INFLUXDB_HOST", '192.168.200.131'),
            crawler.settings.get("INFLUXDB_POST", 8086),
            crawler.settings.get("INFLUXDB_USERNAME", ""),
            crawler.settings.get("INFLUXDB _PASSWORD", ""),
            crawler.settings.get("INFLUXDB_DB", 'db_roc'))

    def process_item(self, item, response, spider):
        site = (item.get("meta", {}).get("tags") or {}).get("source_site_code")
        if site:
            table_name = self.settings.get("MESUREMENT", "roc_ingestion")
            tags = {"app": self.__class__.__name__, "item_type": "item",
                    "crawl_type": item.get("meta", {}).get("type"), "site": site}
            fields = {"crawlid": item["crawlid"], "value": 1, "etc": ""}
            self.client.write_points([{
                "measurement": table_name,
                "tags": tags,
                "time": datetime.datetime.utcnow(),
                "fields": fields
            }])
        return item


class AmazonMiddleware(ItemProcessMiddleware):
    def process_item(self, item, response, spider):
        node_ids = item["node_ids"]
        brand = item["brand"]
        if not (node_ids and brand):
            self.logger.info("%s miss node_ids or brand, node_ids: %s, brand: %s"%(item["url"], node_ids, brand))
        return item


class AreatrendMiddleware(ItemProcessMiddleware):

    def process_item(self, item, response, spider):
        data = spider.redis_conn.hget("areatrend:product", item["product_id"])
        if data:
            item["ware"] = json.loads(data)
        return item