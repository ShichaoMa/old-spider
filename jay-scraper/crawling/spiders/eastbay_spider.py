# -*- coding:utf-8 -*-
import os
from toolkit import re_search, safely_json_loads

from . import JaySpider
from ..items.eastbay_item import EastbayItem, image_urls_processor
from ..utils import enrich_wrapper, CustomLoader, re_exchange, ItemCollectorPath


class EastbaySpider(JaySpider):
    name = "eastbay"
    # 商品详情页链接的xpath表达式或re表达式
    item_xpath = (
        '//*[@id="endeca_search_results"]/ul/li/a[1]/@href',
    )
    # 商品下一页的xpath表达式
    page_xpath = (
        '//a[@class="next"]/@href',
    )

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
            'crawling.downloadermiddlewares.LimitedUserAgentMiddleware': 400,
            'crawling.downloadermiddlewares.NewFixedRetryMiddleware': 510,
            "crawling.downloadermiddlewares.CustomProxyMiddleware": 588,
            'crawling.downloadermiddlewares.CustomRedirectMiddleware': 600,
        },
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=EastbayItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_re("NBR", r'var model_nbr = (.*);')
        item_loader.add_value("NBR", response.meta["url"], re=r"product/model:(\d+)")
        item_loader.add_value("product_id", "")
        item_loader.add_re("model", r'var model = (.*);')
        item_loader.add_re("styles", r'var styles = (.*);')
        item_loader.add_xpath("title", [
            '//*[@id="model_name"]/text()',
            '//h1[@id="product_title"]/text()',
        ])
        # if not response.xpath('//div[@id="product_mixedmedia"]//img/@data-blzsrc'):
        #     item_loader.add_xpath("image_urls", '//div[@id="product_mixedmedia"]//img/@src')
        # item_loader.add_xpath("description", "//meta[@name='description']/@content")
        item_loader.add_value("INET_COPY", "")
        skus = [x for x in safely_json_loads(re_exchange(
            response.selector.re(r'var model = (.*);'))).get(
            "ALLSKUS", response.selector.re(r"var sku_nbr = '(.*)';")) if x.strip()]
        for sku in skus:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "image_urls#%s" % sku))] = item_loader
        return [{"url": "http://images.footlocker.com/is/image/EBFL2/%s?req=set,json,UTF-8" % sku,
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "image_urls#%s" % sku))}} for sku in skus]

    @enrich_wrapper
    def enrich_image_urls(self, item_loader, response):
        self.logger.debug("Start to enrich image_urls and color_images. ")
        item_loader.add_re("image_urls", r'\((.*?),""\)')
        item_loader.add_value("color_images", (
            re_search(r"(?<=EBFL2/)(.*?)(?=\?)", response.url), image_urls_processor(safely_json_loads(
                re_exchange(response.selector.re(r'\((.*?),""\)'))))), lambda x: [x])

    def need_duplicate(self, url):
        return re_search(r"product/model:(\d+)", url)
