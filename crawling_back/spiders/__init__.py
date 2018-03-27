# -*- coding:utf-8 -*-
# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import time
from hashlib import sha1
from urllib.parse import urlparse

from scrapy.spiders import Spider
from scrapy import signals, Request
from scrapy.exceptions import DontCloseSpider, IgnoreRequest
from scrapy.utils.response import response_status_message

from .fingerprint import FINGERPRINT
from .exception_process import parse_method_wrapper
from .utils import post_es, LoggerDescriptor, url_arg_increment, url_item_arg_increment, \
    url_path_arg_increment, enrich_wrapper, ItemCollector, ItemCollectorPath, is_debug


class JaySpider(Spider):

    name = "jay"
    need_duplicate = False
    item_xpath = tuple()
    page_xpath = tuple()
    proxy = None
    change_proxy = None
    log = LoggerDescriptor()
    debug = is_debug()

    def __init__(self, *args, **kwargs):
        Spider.__init__(self, *args, **kwargs)
        self.redis_conn = None

    @property
    def logger(self):
        return self.log

    def _set_crawler(self, crawler):
        super(JaySpider, self)._set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)

    def set_redis(self, redis_conn):
        self.redis_conn = redis_conn

    def spider_idle(self):
        if self.settings.getbool("IDLE", True):
            print('Don\'t close spider......')
            raise DontCloseSpider

    def duplicate_filter(self, response, url, func):
        crawlid = response.meta["crawlid"]
        common_part = func(url)

        if self.redis_conn.sismember("crawlid:%s:model" % crawlid, common_part):
            return True
        else:
            self.redis_conn.sadd("crawlid:%s:model" % crawlid, common_part)
            self.redis_conn.expire("crawlid:%s:model" % crawlid,
                                   self.crawler.settings.get("DUPLICATE_TIMEOUT", 60 * 60))
            return False

    @staticmethod
    def get_base_loader(response):
        pass

    def extract_item_urls(self, response):
        return [response.urljoin(x) for x in set(response.xpath("|".join(self.item_xpath)).extract())]

    @staticmethod
    def adjust(response):
        if "if_next_page" in response.meta:
            del response.meta["if_next_page"]
        else:
            response.meta["seed"] = response.url

        # 防止代理继承  add at 16.10.26
        response.meta.pop("proxy", None)
        response.meta["callback"] = "parse_item"
        response.meta["priority"] -= 20

    def extract_page_urls(self, response, effective_urls, item_urls):
        xpath = "|".join(self.page_xpath)

        if xpath.count("?") == 1:
            next_page_urls = [url_arg_increment(xpath, response.url)] if len(effective_urls) else []
        elif xpath.count("~="):
            next_page_urls = [url_path_arg_increment(xpath, response.url)] if len(effective_urls) else []
        elif xpath.count("/") > 1:
            next_page_urls = [response.urljoin(x) for x in set(response.xpath(xpath).extract())] if len(effective_urls) else []
        else:
            next_page_urls = [url_item_arg_increment(xpath, response.url, len(item_urls))] if len(effective_urls) else []

        response.meta["if_next_page"] = True
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        return next_page_urls

    @parse_method_wrapper
    def parse(self, response):
        self.logger.debug("Start response in parse. ")
        item_urls = self.extract_item_urls(response)
        if not response.meta.get("full", True):
            self.logger.debug("Filtering exists items. ")
            new_urls = [i for i in item_urls if not post_es(
                self.crawler.settings.get("ES_HOST", "192.168.200.153"), self.crawler.settings.getint("ES_PORT", 9200),
                sha1(FINGERPRINT.get(self.name, lambda x: x)(i).encode("utf-8")).hexdigest())]
            self.logger.debug("%s items have been skipped. " % (len(item_urls) - len(new_urls)))
            item_urls = new_urls
        self.adjust(response)
        # 增加这个字段的目的是为了记住去重后的url有多少个，如果为空，对于按参数翻页的网站，有可能已经翻到了最后一页。
        effective_urls = []
        for item_url in item_urls:
            if self.need_duplicate:
                if self.duplicate_filter(response, item_url, self.need_duplicate):
                    continue
            response.meta["url"] = item_url
            self.crawler.stats.inc_total_pages(response.meta['crawlid'])
            effective_urls.append(item_url)
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          errback=self.errback)
        next_page_urls = self.extract_page_urls(response, effective_urls, item_urls) or []

        for next_page_url in next_page_urls:
            response.meta["url"] = next_page_url
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)
            # next_page_url有且仅有一个，多出来的肯定是重复的
            break

    @enrich_wrapper
    def enrich_base_data(self, item_loader, response):
        item_loader.add_value('spiderid', response.meta.get('spiderid'))
        item_loader.add_value('url', response.meta.get("url"))
        item_loader.add_value("seed", response.meta.get("seed", ""))
        item_loader.add_value("timestamp", time.strftime("%Y%m%d%H%M%S"))
        item_loader.add_value('status_code', response.status)
        item_loader.add_value("status_msg", response_status_message(response.status))
        item_loader.add_value('domain', urlparse(response.url).hostname.split(".", 1)[1])
        item_loader.add_value('crawlid', response.meta.get('crawlid'))
        item_loader.add_value('response_url', response.url)
        item_loader.add_value("item_type", getattr(self, "item_type", "product"))
        item_loader.add_value("proxy", response.meta.get("proxy"))
        item_loader.add_value("fingerprint", sha1(FINGERPRINT.get(self.name, lambda x: x)(
            response.url).encode("utf-8")).hexdigest())
        meta = dict()
        code_list = ["tags", "extend", "full", "type", "upc", "ean", "mpn", "roc_id", "all_sku"]
        for code in code_list:
            meta[code] = response.meta.get(code)
        item_loader.add_value("meta", meta)
        if response.meta.get("seed", "") or response.meta.get("type") == "explore":
            collection_name = "jay_%ss" % response.meta.get('spiderid')
        else:
            collection_name = "jay_%s_updates" % response.meta.get('spiderid')
        item_loader.add_value("collection_name", collection_name)

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        pass

    @parse_method_wrapper
    def parse_item(self, response):
        response.meta["request_count_per_item"] = 1
        base_loader = self.get_base_loader(response)
        meta = response.request.meta
        item_collector = ItemCollector()
        meta["item_collector"] = item_collector
        meta["path"] = ItemCollectorPath()
        item_collector.add_item_loader(meta["path"], base_loader)
        self.enrich_base_data(base_loader, response)
        requests = self.enrich_data(base_loader, response)
        return self.yield_item(requests, item_collector, response)

    @parse_method_wrapper
    def parse_next(self, response):
        response.meta["request_count_per_item"] += 1
        meta = response.request.meta
        item_collector = meta["item_collector"]
        path = meta["path"]
        loader = item_collector.item_loader(path)
        prop = path.last_prop()
        requests = getattr(self, "enrich_%s"%prop)(loader, response)
        return self.yield_item(requests, item_collector, response)

    def yield_item(self, requests, item_collector, response):
        if requests:
            item_collector.add_requests(requests)
        if item_collector.have_request():
            req = item_collector.pop_request()
            response.request.meta.update(req["meta"])
            response.request.meta["priority"] += 1
            req["meta"] = response.request.meta
            req["callback"] = "parse_next"
            req["errback"] = "errback"
            return Request(**req)
        else:
            item = item_collector.load_item()
            if item.get("status_code") != 999:
                self.logger.info("crawlid: %s, product_id: %s, %s requests send for successful yield item" % (
                    item.get("crawlid"), item.get("product_id", "unknow"), response.meta.get("request_count_per_item", 1)))
                self.crawler.stats.inc_crawled_pages(response.meta['crawlid'])
            else:
                item["status_msg"] = "".join(response.xpath("//html/body/p/text()").extract())
            return item

    def errback(self, failure):
        if failure and failure.value and hasattr(failure.value, 'response'):
            response = failure.value.response

            if response:
                loader = self.get_base_loader(response)
                self.enrich_base_data(loader, response)
                item = loader.load_item()
                if item["status_msg"].count("Unknown Status"):
                    item["status_msg"] = "errback: %s"% failure.value
                self.logger.error("errback: %s" % item)
                if not isinstance(failure.value, IgnoreRequest):
                    self.crawler.stats.inc_crawled_pages(response.meta['crawlid'])
                return item
            else:
                self.logger.error("failure has NO response")
        else:
            self.logger.error("failure or failure.value is NULL, failure: %s" % failure)
