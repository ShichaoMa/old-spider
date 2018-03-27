# -*- coding:utf-8 -*-
import os
import hashlib
from toolkit import re_search

from . import JaySpider
from ..items.watchstation_item import WatchstationItem
from ..utils import CustomLoader, enrich_wrapper, url_item_arg_increment, ItemCollectorPath


class WatchstationSpider(JaySpider):
    name = "watchstation"
    item_xpath = ('//div[@class="prodName"]/a/@href',)
    path = "/webapp/wcs/stores/servlet/FSAJAXService"
    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
            'crawling.spidermiddlewares.InfluxDBMiddleware': 990,
        }
    }

    def extract_page_url(self, response, effective_urls, item_urls):
        if response.xpath('//div[@class="pagination"]'):
            if response.xpath('//div[@class="pagination"]/a[contains(text(), "Next")]'):
                url = url_item_arg_increment("No=0", response.url, 20)
            else:
                return None
        else:
            url = "".join(response.selector.re(r"var productServiceURL = \"(.*)\";"))
        response.meta["if_next_page"] = True
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        return url

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=WatchstationItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("title", '//h1[@class="pdpBrandTitle"]/a/text()')
        product_id = re_search(r'"productId":(\d+)', response.body)
        item_loader.add_value("product_id", product_id)
        item_loader.add_xpath("part_number", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("mpn", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("model_number", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("old_price", '//div[@id="priceDetails"]/span[@class="strike"]/text()')
        item_loader.add_xpath("price", ['//div[@id="priceDetails"]/span[@class="newPrice"]/text()',
                                        '//span[@class="price"]/text()'])
        item_loader.add_xpath("feature", '//div[@class="productSpecs"]')
        spans = [i.strip() for i in response.xpath('//div[@class="productSpecs"]/span/text()').extract() if i.strip()]
        specs = [[spans[2*i], spans[2*i+1]] for i in range(len(spans)//2)]
        item_loader.add_value("specs", specs)
        item_loader.add_xpath("description", '//div[@class="productDescription"]/p')
        image_url = "http://fossil.scene7.com/is/image/FossilPartners/%s_is?req=set,json,UTF-8&wsiAsset_pdpdetail&" \
                    "labelkey=label&id=%s&handler=s7classics7sdkJSONResponse" % (
            re_search(r'"partnumber":"(\w+)"', response.body), product_id)
        response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
            str(response.meta["path"]), "image_urls#%s" % product_id))] = item_loader
        return [{"url": image_url, "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "image_urls#%s" % product_id))}}]

    @enrich_wrapper
    def enrich_image_urls(self, item_loader, response):
        item_loader.add_re("image_urls", r's7classics7sdkJSONResponse\((.*),"\d+"\);')
