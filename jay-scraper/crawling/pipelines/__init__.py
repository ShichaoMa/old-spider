# -*- coding:utf-8 -*-
import os
import sys
import time
import json
import shutil
import datetime

from scrapy.signals import spider_closed

from kafka import KafkaProducer
from kafka.common import KafkaUnavailableError

from ..utils import CustomLogger, ItemEncoder


class BasePipeline(object):

    def __init__(self, settings):
        self.settings = settings
        self.logger = CustomLogger.from_crawler(self.crawler)

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=spider_closed)
        return o

    def process_item(self, item, spider):
        pass

    def spider_closed(self):
        pass


class FilePipeline(BasePipeline):
    def process_item(self, item, spider):
        open("test.json", "w").write(json.dumps(dict(item), indent=1))
        return item


class JSONPipeline(BasePipeline):
    """
    数据存储到json中
    """
    def __init__(self, settings):
        super(JSONPipeline, self).__init__(settings)
        self.logger.debug("Setup json pipeline.")
        self.files = {}
        self.setup()

    def create(self, crawlid):
        file_name = "task/%s_%s.json" % (self.crawler.spidercls.name, crawlid)
        if os.path.exists(file_name):
            shutil.copy(file_name, "%s.%s"%(file_name, time.strftime("%Y%m%d%H%M%S")))

        fileobj = open(file_name, "w")
        self.files[file_name] = fileobj
        return fileobj

    def setup(self):
        if not os.path.exists("task"):
            os.mkdir("task")

    def process_item(self, item, spider):
        self.logger.debug("Processing item in JSONPipeline.")
        crawlid = item["crawlid"]
        file_name = "task/%s_%s.json" % (spider.name, crawlid)
        fileobj = self.files.get(file_name) or self.create(crawlid)
        fileobj.write("%s\n"%json.dumps(dict(item)))
        return item

    def spider_closed(self):
        self.logger.info("close file...")
        for fileobj in self.files.values():
            fileobj.close()


class KafkaPipeline(BasePipeline):
    """
        Pushes a serialized item to appropriate Kafka topics.
    """

    def __init__(self, settings):
        super(KafkaPipeline, self).__init__(settings)
        self.logger.debug("Setup kafka pipeline")
        try:
            self.producer = KafkaProducer(bootstrap_servers=settings['KAFKA_HOSTS'].split(","), retries=3)
        except KafkaUnavailableError:
            self.logger.error("Unable to connect to Kafka in Pipeline, raising exit flag. ")
            sys.exit(1)

    def errback(self, exception):
        self.logger.error("Error in kafka feature: %s. " % str(exception))

    def callback(self, value):
        self.logger.debug("Success in kafka feature: %s. " % str(value))

    def process_item(self, item, spider):
        command = item.get("command")
        topic = self.settings.get("EXPORT_TOPICS").get(command, self.settings.get("EXPORT_TOPIC"))
        if not command:
            item["timestamp"] = datetime.datetime.fromtimestamp(item["timestamp"]).strftime("%Y%m%d%H%M%S")
        self.logger.debug("Processing item in KafkaPipeline to %s"%topic)
        try:
            message = json.dumps(item, cls=ItemEncoder)
        except UnicodeDecodeError:
            message = json.dumps(item, cls=ItemEncoder, encoding="gbk")
        future = self.producer.send(topic, message.encode())
        future.add_callback(self.callback)
        future.add_errback(self.errback)
        return item

    def spider_closed(self):
        self.producer.close()


class UPCPipeline(BasePipeline):

    def __init__(self, settings):
        super(UPCPipeline, self).__init__(settings)
        self.settings = settings
        self.logger.debug("Setup UPC pipeline")

    def process_item(self, item, spider):
        # 调用keeper的api来更新upc的状态为2
        pass


class ScreenshotPipeline(object):
    """Pipeline that uses Splash to render screenshot of
    every Scrapy item."""

    SPLASH_URL = "http://httpbin.org/ip"

    def process_item(self, item, spider):
        meta = {"bindaddress": ("192.168.200.94", 0), "priority": 1000}
        request = scrapy.Request(self.SPLASH_URL, meta=meta)
        dfd = spider.crawler.engine.download(request, spider)
        dfd.addBoth(self.return_item, item)
        return dfd

    def return_item(self, response, item):
        import pdb
        pdb.set_trace()
        return item