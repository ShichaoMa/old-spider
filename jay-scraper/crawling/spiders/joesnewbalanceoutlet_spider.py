# -*- coding:utf-8 -*-
import os
import hashlib

from urllib.parse import urlencode
from toolkit import safely_json_loads

from . import JaySpider
from ..items.joesnewbalanceoutlet_item import JoesnewbalanceoutletiItem
from ..utils import CustomLoader, enrich_wrapper, ItemCollectorPath, xpath_exchange


class JoesnewbalanceoutletSpider(JaySpider):
    name = "joesnewbalanceoutlet"
    item_xpath = ('//a[@class="impression"]/@href',)
    page_xpath = (r'(.*?)(Page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=JoesnewbalanceoutletiItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_re("variants", r"variants: (\[.*?\]),")
        item_loader.add_re("colors", r"children: (\[.*?\]),")
        item_loader.add_xpath("product_id", '//input[@name="MasterID"]/@value')
        item_loader.add_re("prices", r"'price': '(.*?)',")
        item_loader.add_xpath("list_prices", '//span[@class="origPrice"]/span/text()')
        item_loader.add_xpath("description", '//div[@id="Description"]/p/text()')
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("features", '//div[@class="hideOnMobile"]/div/ul[@class="productFeaturesDetails"]/li/text()')
        item_loader.add_re("color_images", r"images: (\[.*?\]),")
        item_loader.add_value("image_urls", "")
        item_loader.add_value("skus", "")
        color_urls = set(response.urljoin(url) for url in response.xpath('//div[@class="similarItem"]/a/@href').extract())
        req_metas = list()
        for color_url in color_urls:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))] = item_loader
        for color_url in color_urls:
            req_metas.append({"url": color_url,
             "meta": {"path": ItemCollectorPath(os.path.join(
                 str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                     color_url.encode("utf-8")).hexdigest()))}})
        stock_url = "https://www.joesnewbalanceoutlet.com/product/getInventoryQuantity"
        skus = safely_json_loads("".join(response.selector.re(r"variants: (\[.*?\]),")))
        __RequestVerificationToken = xpath_exchange(response.xpath("//input[@name='__RequestVerificationToken']/@value"))
        for sku in skus:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "skus#%s" % sku["v"]))] = item_loader
        for sku in skus:
            req_metas.append({"url": stock_url, "body": urlencode(
                {"__RequestVerificationToken": __RequestVerificationToken,
                 "VariantID": sku["v"]}), "headers": {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                              "method": "post", "meta": {"path": ItemCollectorPath(os.path.join(
                                  str(response.meta["path"]), "skus#%s" % sku["v"])), "sku": sku["v"]}})
        return req_metas

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        self.logger.debug("Start to enrich colors. ")
        item_loader.add_re("prices", r"'price': '(.*?)',")
        item_loader.add_xpath("list_prices", '//span[@class="origPrice"]/span/text()')
        item_loader.add_re("variants", r"variants: (\[.*?\]),")
        stock_url = "https://www.joesnewbalanceoutlet.com/product/getInventoryQuantity"
        skus = safely_json_loads("".join(response.selector.re(r"variants: (\[.*?\]),")))
        __RequestVerificationToken = xpath_exchange(response.xpath("//input[@name='__RequestVerificationToken']/@value"))
        req_metas = list()
        for sku in skus:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "skus#%s" % sku["v"]))] = item_loader
        for sku in skus:
            req_metas.append({"url": stock_url, "body": urlencode(
                {"__RequestVerificationToken": __RequestVerificationToken,
                 "VariantID": sku["v"]}),
                              "headers": {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                              "method": "post", "meta": {"path": ItemCollectorPath(os.path.join(
                    str(response.meta["path"]), "skus#%s" % sku["v"])), "sku": sku["v"]}})
        return req_metas

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        item_loader.add_value("stock", {response.meta["sku"]: response.body})