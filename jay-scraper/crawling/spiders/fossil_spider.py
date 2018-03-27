# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.fossil_item import FossilItem
from ..utils import CustomLoader, enrich_wrapper


class FossilSpider(JaySpider):
    name = "fossil"
    item_xpath = ('//a[@class="link-product-result-path text-ellipsis"]/@href',)
    page_xpath = (r'1~=(.pageNumber)(\d+)(\.html)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=FossilItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id", r'"itemID" : "(\w+)"')
        item_loader.add_re("part_number", r'"itemID" : "(\w+)"')
        item_loader.add_re("sku_collection", r'"products" : (\[[\S\s]* \]),\s*"borderFreePrices"')
        item_loader.add_xpath("description", '//div[@class="beauty-copy col-xs-12"]')
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("detail", '//div[@class="visible-xs border-bottom"]')
        item_loader.add_xpath("image_urls", '//img[@class="img-responsive"]/@src')
