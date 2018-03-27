# -*- coding:utf-8 -*-
import os

from toolkit import re_search, safely_json_loads, duplicate

from . import JaySpider
from ..items.moncler_item import MonclerItem
from ..utils import CustomLoader, enrich_wrapper, ItemCollectorPath, xpath_exchange


class MonclerSpider(JaySpider):
    name = "moncler"
    item_xpath = ('//section[@class="products "]/ul/li/div/a/@href',)
    page_xpath = ('//a/b/c',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=MonclerItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id", r'"LandingPartNumber":"(\d+)"')
        item_loader.add_value("product_id", re_search(r"_cod(\d+)", response.meta["url"]))
        item_loader.add_re("part_number", r'"LandingPartNumber":"(\d+)"')
        item_loader.add_xpath("title", '//h1/span/text()')
        item_loader.add_xpath("description", '//p/span[@class="value"]/text()')
        item_loader.add_xpath("feature", '//div[@class="compositionInfo"]/span[@class="text"]')
        image_set_url = "https://store.moncler.com/yTos/Plugins/itemPlugin/RenderProductAlternativeShotsAsync?" \
                        "partNumber=%s&imageOptions.Height=70&imageOptions.Width=55"
        req_meta = list()
        for color in response.xpath('//ul/li/@data-ytos-color-model').extract():
            color_id = safely_json_loads(color)["ProductColorPartNumber"]
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "image_urls#%s"%color_id))] = item_loader
            req_meta.append({"url": response.urljoin(image_set_url%color_id),
                             "meta": {"path": ItemCollectorPath(
                                 os.path.join(str(response.meta["path"]), "image_urls#%s" % color_id))}})

        part_number = re_search(r'"LandingPartNumber":"(\d+)"', response.body)
        if part_number:
            skus_url = "https://store.moncler.com/yTos/api/Plugins/ItemPluginApi/" \
                       "ProductAvailability/?partNumber=%s&siteCode=MONCLER_US" % part_number
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "skus"))] = item_loader
            req_meta.append({"url": response.urljoin(skus_url),
                             "meta": {"path": ItemCollectorPath(os.path.join(str(response.meta["path"]), "skus"))}})
        return req_meta

    @enrich_wrapper
    def enrich_image_urls(self, item_loader, response):
        item_loader.add_value("color_images", {re_search(
            r'partNumber&quot;:&quot;(\d+)&quot', response.body): response.xpath('//ul/li/img/@src').extract()})

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        skus = safely_json_loads(response.body)
        item_loader.add_value("skus", skus)
        meta_list = list()
        for color_id in duplicate(skus, keep=lambda x:x["colorPartNumber"], key=lambda x: x["colorPartNumber"]):
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