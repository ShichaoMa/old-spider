# -*- coding:utf-8 -*-
from toolkit import re_search

from . import JaySpider
from ..items.nordstrom_item import NordstromItem
from ..utils import CustomLoader, enrich_wrapper


class NordstromSpider(JaySpider):
    name = "nordstrom"
    item_xpath = ('//a[@class="product-href"]/@href', )
    page_xpath = (r'(.*?)(page=1)(\d+)(.*)', )

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=NordstromItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("initialData", r'"initialData":({.*?})}\)')
        item_loader.add_value("product_name", "")
        item_loader.add_value("product_id", "")
        item_loader.add_value("description", "")
        item_loader.add_value("features", "")
        item_loader.add_value("skus", "")
        item_loader.add_value("color_images", "")
        item_loader.add_value("image_urls", "")
