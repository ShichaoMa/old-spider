# -*- coding:utf-8 -*-
import os
from toolkit import re_search, safely_json_loads

from . import JaySpider
from ..items.armaniexchange_item import ArmaniexchangeiItem
from ..utils import CustomLoader, enrich_wrapper, ItemCollectorPath


class ArmaniexchangeSpider(JaySpider):
    name = "armaniexchange"
    item_xpath = ('//article[@class="item"]/a/@href',)
    page_xpath = ("//a/b/c",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=ArmaniexchangeiItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_value("product_id", response.url, re=r"_(\w+)")
        item_loader.add_xpath("part_number", '//div[@class="content details"]//li[5]/text()')
        item_loader.add_xpath("color", '//ul/li/div/div[@class="description"]/text()')
        item_loader.add_xpath("title", '//h1/div/span/text()')
        item_loader.add_xpath("description", '//div[@class="content"]/div/span[@class="value"]')
        item_loader.add_xpath("detail", '//div[@class="content details"]')
        item_loader.add_xpath("image_urls", '//ul[@class="alternativeImages"]/li/img/@srcset')
        item_loader.add_xpath("price", '//div[@class="itemPrice"]//span[@class="price"]/span/text()')
        color_size_url = "https://www.armaniexchange.com/yTos/api/Plugins/ItemPluginApi/GetCombinationsAsync" \
                         "/?siteCode=ARMANIEXCHANGE_US&code10=%s"%re_search(r"_cod(\w+)", response.url)
        path = ItemCollectorPath(os.path.join(str(response.meta["path"]), "color_size"))
        response.meta["item_collector"].add_item_loader(path, item_loader)
        return [{"url": color_size_url,  "meta": {"path": path}}]

    @enrich_wrapper
    def enrich_color_size(self, item_loader, response):
        data = safely_json_loads(response.body)
        item_loader.add_value("color", data["Colors"])
        item_loader.add_value("size", data["Sizes"])