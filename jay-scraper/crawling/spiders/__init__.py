# -*- coding:utf-8 -*-
# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import time
import traceback

from functools import reduce
from urllib.parse import urlparse, urljoin

from scrapy import signals, Request
from scrapy.exceptions import DontCloseSpider, IgnoreRequest
from scrapy.spiders import Spider
from scrapy.utils.response import response_status_message

from toolkit import cache_prop
from toolkit.managers import ExceptContext

from ..utils import CustomLogger, enrich_wrapper, ItemCollector, ItemCollectorPath, \
    url_arg_increment, url_item_arg_increment, url_path_arg_increment, is_debug


class JaySpider(Spider):

    name = "jay"
    need_duplicate = False
    item_xpath = tuple()
    page_xpath = tuple()
    proxy = None
    change_proxy = None
    debug = is_debug()

    def __init__(self, *args, **kwargs):
        Spider.__init__(self, *args, **kwargs)
        self.redis_conn = None

    @cache_prop
    def logger(self):
        return CustomLogger.from_crawler(self.crawler)

    def page_url(self, response):
        return response.url

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

    def extract_page_url(self, response, effective_urls, item_urls):
        """
        返回下一页链接
        :param response:
        :param effective_urls: 当前页有效的item链接
        :param item_urls: 当前页全部item链接
        :return: 返回下一页链接或相关请求属性元组，如(url, callback, method...)
        """
        xpath = "|".join(self.page_xpath)
        page_url = self.page_url(response)
        if len(effective_urls):
            if xpath.count("?") == 1:
                next_page_url = url_arg_increment(xpath, page_url)
            elif xpath.count("~="):
                next_page_url = url_path_arg_increment(xpath, page_url)
            elif xpath.count("/") > 1:
                next_page_url = reduce(
                    lambda x, y: y, (urljoin(page_url, x) for x in set(response.xpath(xpath).extract())), None)
            else:
                next_page_url = url_item_arg_increment(xpath, page_url, len(item_urls))
        else:
            next_page_url = None

        response.meta["if_next_page"] = True
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        return next_page_url

    def log_err(self, func_name, *args):
        self.logger.error("Error in %s: %s. " % (func_name, "".join(traceback.format_exception(*args))))
        return True

    def parse(self, response):
        with ExceptContext(errback=self.log_err) as ec:
            self.logger.debug("Start response in parse. ")
            item_urls = self.extract_item_urls(response)
            self.adjust(response)
            # 增加这个字段的目的是为了记住去重后的url有多少个，如果为空，对于按参数翻页的网站，有可能已经翻到了最后一页。
            effective_urls = [i for i in item_urls
                              if not (self.need_duplicate and self.duplicate_filter(response, i, self.need_duplicate))]
            self.crawler.stats.inc_total_pages(response.meta['crawlid'], len(effective_urls))
            yield from self.gen_requests(
                [dict(url=u, errback="errback") for u in effective_urls], "parse_item", response)

            next_page_url = self.extract_page_url(response, effective_urls, item_urls)
            if next_page_url:
                yield from self.gen_requests([next_page_url], "parse", response)
        if ec.got_err:
            self.crawler.stats.set_failed_download(response.meta, "In parse: " + traceback.format_exc())

    def gen_requests(self, url_metas, callback, response):
        """
        生成requests
        :param url_metas:可以是一个url， 或者(url, callback, method...)元组，顺序为Request参数顺序，
        或者{"url": "...", "method": "GET"...}
        :param callback: 可以统一指定callback
        :param response:
        :return:
        """
        for url_meta in url_metas:
            if isinstance(url_meta, dict):
                url_meta["callback"] = callback
                response.meta["url"] = url_meta["url"]
                yield Request(**url_meta, meta=response.meta)
                continue
            elif not isinstance(url_meta, list):
                url_meta = [url_meta, callback]
            response.meta["url"] = url_meta[0]
            yield Request(*url_meta, meta=response.meta)

    @enrich_wrapper
    def enrich_base_data(self, item_loader, response):
        item_loader.add_value('spiderid', response.meta.get('spiderid'))
        item_loader.add_value('url', response.meta.get("url"))
        item_loader.add_value("seed", response.meta.get("seed", ""))
        item_loader.add_value("timestamp", time.time())
        item_loader.add_value('status_code', response.status)
        item_loader.add_value("status_msg", response_status_message(response.status))
        item_loader.add_value('domain', urlparse(response.url).hostname.split(".", 1)[1])
        item_loader.add_value('crawlid', response.meta.get('crawlid'))
        item_loader.add_value('response_url', response.url)
        item_loader.add_value("item_type", getattr(self, "item_type", "product"))
        item_loader.add_value("proxy", response.meta.get("proxy"))
        item_loader.add_value("meta", response.meta.get("tags"))

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        pass

    def parse_item(self, response):
        with ExceptContext(errback=self.log_err) as ec:
            response.meta["request_count_per_item"] = 1
            base_loader = self.get_base_loader(response)
            meta = response.request.meta
            item_collector = ItemCollector()
            meta["item_collector"] = item_collector
            meta["path"] = ItemCollectorPath()
            item_collector.add_item_loader(meta["path"], base_loader)
            self.enrich_base_data(base_loader, response)
            requests = self.enrich_data(base_loader, response)
            result = self.yield_item(requests, item_collector, response)
        if ec.got_err:
            meta = response.meta
            self.crawler.stats.set_failed_download(
                response.meta, "In parse_item: " +
                               "".join(traceback.format_exception(*ec.err_info)))
        else:
            return result

    def parse_next(self, response):
        with ExceptContext(errback=self.log_err) as ec:
            response.meta["request_count_per_item"] += 1
            meta = response.request.meta
            item_collector = meta["item_collector"]
            path = meta["path"]
            loader = item_collector.item_loader(path)
            prop = path.last_prop()
            requests = getattr(self, "enrich_%s"%prop)(loader, response)
            result = self.yield_item(requests, item_collector, response)
        if ec.got_err:
            self.crawler.stats.set_failed_download(
                response.meta, "In parse_next: " +
                               "".join(traceback.format_exception(*ec.err_info)))
        else:
            return result

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
