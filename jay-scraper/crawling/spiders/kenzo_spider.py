# -*- coding:utf-8 -*-
import os
import time
import hashlib

from functools import partial
from scrapy.loader.processors import MapCompose
from toolkit import strip, rid

from . import JaySpider
from ..items.kenzo_item import KenzoItem, KenzoColorItem
from ..utils import CustomLoader, enrich_wrapper, ItemCollectorPath


class KenzoSpider(JaySpider):
    name = "kenzo"
    item_xpath = ('//a[@class="product"]/@href',)
    page_xpath = ('//a[@id="lazyloadTemplate"]/@data-href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=KenzoItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id", r"id: '(\w+)'")
        item_loader.add_xpath("part_number", '//span[@class="MFC"]/text()')
        item_loader.add_xpath("title", "//h1/text()")
        item_loader.add_xpath("description", '//div[@itemprop="description"]/div/text()')
        item_loader.add_value("color_images", "")
        color_urls = response.xpath('//div[contains(@class, "kz-pp-fiche")]//ul[@id="va-color"]/li/@data-value').extract()
        for color_url in color_urls:
            color_url = color_url + "&format=ajax"
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))] = CustomLoader(item=KenzoColorItem())
        return [{"url": color_url + "&format=ajax",
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                         (color_url + "&format=ajax").encode("utf-8")).hexdigest()))}} for color_url in color_urls]

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        item_loader.add_value("status_code", response.status)
        item_loader.add_value("url", response.url)
        item_loader.add_value("timestamp", time.strftime("%Y%m%d%H%M%S"))
        item_loader.add_xpath("image_urls", '//div[@class="row"]//img[@itemprop="image"]/@src')
        item_loader.add_xpath("color", '//div[contains(@class, "kz-pp-fiche")]//ul[@id="va-color"]/li[@class="selected"]/span/text()')
        item_loader.add_xpath("color_id", '//div[contains(@class, "kz-pp-fiche")]//ul[@id="va-color"]/li[@class="selected"]/@data-color3dobject')
        item_loader.add_xpath("sizes", '//div[contains(@class, "kz-pp-fiche")]//select[@id="va-size"]/option/text()')
        item_loader.add_xpath("availabilities", '//div[contains(@class, "kz-pp-fiche")]//select[@id="va-size"]/option/@data-custom-class')
        item_loader.add_xpath("price", '//div[@class="kz-pp-fiche-price"]/div[@class="price"]//text()', MapCompose(strip), MapCompose(partial(rid, old="\u20ac", new="$")))