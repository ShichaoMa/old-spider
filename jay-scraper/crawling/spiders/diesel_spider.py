# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.diesel_item import DieselItem
from ..utils import CustomLoader, enrich_wrapper


class DieselSpider(JaySpider):
    name = "diesel"
    item_xpath = ('//div[@class="packery"]//ul/li/a/@href',)
    page_xpath = ("start=0",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=DieselItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//div[@class="product-content-header"]/h6/text()', re=r"ID:(\w+)")
        item_loader.add_xpath("part_number", '//div[@class="product-content-header"]/h6/text()', re=r"ID:(\w+)")
        item_loader.add_xpath("price", '//div[@class="product-content-header"]//span[@class="price-sales"]/text()')
        item_loader.add_xpath(
            "colors", '//ul[@class="swatches Color color-slides jcarousel-skin-tango"]/li/a/@data-lgimg')
        item_loader.add_xpath("sizes", '//ul[@class="swatches swatch-variation size"]/li/a/text()')
        item_loader.add_xpath("title", '//div[@class="product-discription clearfix "]/h2/text()')
        item_loader.add_xpath("image_urls", '//ul[@id="product-view"]/li/a/@data-href')
        item_loader.add_xpath("mpn", '//div[@class="product-content-header"]/h6/text()', re=r"ID:(\w+)")
        item_loader.add_xpath("model_number", '//div[@class="product-content-header"]/h6/text()', re=r"ID:(\w+)")
        item_loader.add_xpath("description", '//li[@class="bullet-list-none"]/p/span/text()')
        item_loader.add_xpath("features", '//li[not(@class)]/p/span/text()')

    def need_duplicate(self, url):
        return url