# -*- coding:utf-8 -*-
import sys
import json
import traceback

from scrapy.signals import spider_closed

from kafka import KafkaProducer
from kafka.common import KafkaUnavailableError

from ..utils import Logger, ItemEncoder


class BasePipeline(object):

    def __init__(self, settings):
        self.logger = Logger.from_crawler(self.crawler)

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
        open("test.json", "w").write(json.dumps(dict(item)))
        return item


class KafkaPipeline(BasePipeline):
    """
        Pushes a serialized item to appropriate Kafka topics.
    """

    def __init__(self, settings):
        super(KafkaPipeline, self).__init__(settings)
        self.settings = settings
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
        try:
            self.logger.debug("Processing item in KafkaPipeline")
            try:
                message = json.dumps(item, cls=ItemEncoder)
            except UnicodeDecodeError:
                message = json.dumps(item, cls=ItemEncoder, encoding="gbk")
            firehose_topic = self.settings.get("EXPORT_TOPIC", "jay_firehose_ingress")
            future = self.producer.send(firehose_topic, message.encode("utf-8"))
            future.add_callback(self.callback)
            future.add_errback(self.errback)
        except Exception:
            msg = "Error heppend in pipline, Error: %s"%traceback.format_exc()
            self.logger.error(msg)
            spider.crawler.stats.set_failed_download(
                meta=item, reason=msg, _type="pipeline")
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