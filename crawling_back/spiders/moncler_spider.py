# -*- coding:utf-8 -*-
import os

from scrapy.loader.processors import MapCompose

from toolkit import re_search, safely_json_loads, duplicate

from . import JaySpider
from ..items.moncler_item import MonclerItem
from .utils import CustomLoader, enrich_wrapper, ItemCollectorPath, xpath_exchange


class MonclerSpider(JaySpider):
    name = "moncler"
    item_xpath = ('//section[@class="products "]/ul/li/div/a/@href',)
    page_xpath = ('//a/b/c',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=MonclerItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id",r'"LandingPartNumber":"(\d+)"')
        item_loader.add_re("part_number", r'"LandingPartNumber":"(\d+)"')
        item_loader.add_xpath("title", '//h1/span/text()')
        item_loader.add_xpath("description", '//p/span[@class="value"]')
        item_loader.add_xpath("product_images", '//div[@class="alternativeProductShots"]//img/@src')
        item_loader.add_xpath("feature", '//div[@class="compositionInfo"]/span[@class="text"]')
        item_loader.add_xpath("colors", '//ul/li/@data-ytos-color-model')
        item_loader.add_value("image_urls", "")
        item_loader.add_value("color_images", "")

        skus_url = "https://store.moncler.com/yTos/api/Plugins/ItemPluginApi/" \
                  "ProductAvailability/?partNumber=%s&siteCode=MONCLER_US"%re_search(
                    r'"LandingPartNumber":"(\d+)"', response.body)

        response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
            str(response.meta["path"]), "skus"))] = item_loader
        return [{"url": response.urljoin(skus_url),
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "skus"))}}]

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        skus = safely_json_loads(response.body)
        item_loader.add_value("skus", skus)
        meta_list = list()
        for color_id in duplicate(skus, keep=lambda x:x["colorPartNumber"], key=lambda x:x["colorPartNumber"]):
            price_url = "https://store.moncler.com/yTos/Plugins/ItemPlugin/RenderItemPrice?s" \
                        "iteCode=MONCLER_US&code10=%s&options.priceType=RenderItemPrice"%color_id
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "prices#%s"%color_id))] = item_loader
            meta_list.append({"url": response.urljoin(price_url), "meta": {"path": ItemCollectorPath(os.path.join(
                         str(response.meta["path"]), "prices#%s"%color_id))}})
        return meta_list

    @enrich_wrapper
    def enrich_prices(self, item_loader, response):
        prices = {re_search(r"code10=(\d+)", response.url): xpath_exchange(response.xpath('//span[@class="value"]/text()'))}
        item_loader.add_value("prices", prices)