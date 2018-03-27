# -*- coding:utf-8 -*-
import os
import copy
import json
import hashlib

from toolkit import safely_json_loads, re_search

from . import JaySpider
from ..items.bluefly_item import BlueflyItem, BlueflyColorItem
from ..utils import CustomLoader, enrich_wrapper, xpath_exchange, ItemCollectorPath
import scrapy

class BlueflySpider(JaySpider):
    name = "bluefly"
    item_xpath = ('//ul[@class="mz-productlist-list mz-l-tiles"]/li//a[@class="mz-productlisting-title"]/@href',)
    page_xpath = ('//*[@id="page-content"]//a[@rel="next"]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=BlueflyItem())

    def descartes(self, options, new_option):
        while options:
            option = options.pop(0)
            for value in option["values"]:
                opt = copy.deepcopy(new_option)
                opt.append({"attributeFQN": option["attributeFQN"], "value": int(value["value"])})
                if options:
                    yield from self.descartes(options, opt)
                else:
                    yield opt

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_value("product_id", re_search(r"/([^/]*?)/p", response.url).replace("-", "").upper())
        color_urls = set(response.xpath('//ul[@class="product-color-list"]/li/a/@href').extract())
        if not color_urls:
            color_urls = [response.url]
        for color_url in color_urls:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))] = CustomLoader(item=BlueflyColorItem())
        return [{"url": response.urljoin(color_url),
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                         color_url.encode("utf-8")).hexdigest()))}} for color_url in color_urls]

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        self.logger.debug("Start to enrich colors. ")
        products = safely_json_loads(xpath_exchange(response.xpath('//script[@id="data-mz-preload-product"]/text()')))
        product_id = re_search(r"var prodId = (\d+);", response.body)
        item_loader.add_value("color_id", product_id)
        item_loader.add_xpath("title", '//div[@class="mz-producttitle"]/text()')
        item_loader.add_xpath("image_urls", '//div[@class="mz-productimages-thumbs"]/a/@data-zoom-image')
        item_loader.add_xpath("color", '//span[@id="xColor"]/text()')
        item_loader.add_xpath("features", '//ul[@data-ui="accordion-content"]/li/text()')
        if products["options"]:
            item_loader.add_value(
                "sizes", dict((value["value"], value["stringValue"]) for value in products["options"][0]["values"]))
            headers = safely_json_loads(re_search(r'"headers":({.*?}),', response.body))
            headers["Content-type"] = "application/json"
            options = [json.dumps({"options": option}) for option in self.descartes(products["options"], list())]
            for option in options:
                response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                    str(response.meta["path"]), "skus#%s" % hashlib.sha1(
                        option.encode("utf-8")).hexdigest()))] = item_loader
            req_meta = list()
            for option in options:
                req_meta.append({
                    "url": "https://www.bluefly.com/api/commerce/catalog/storefront/products/%s/configure" % product_id,
                    "headers": headers,
                    "body": option,
                    "method": "POST",
                    "meta": {"path": ItemCollectorPath(os.path.join(
                         str(response.meta["path"]), "skus#%s" % hashlib.sha1(
                             option.encode("utf-8")).hexdigest()))}})
            return req_meta

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        item_loader.add_value("skus", safely_json_loads(response.body))
