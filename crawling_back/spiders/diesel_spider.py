# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.diesel_item import DieselItem
from .utils import CustomLoader, enrich_wrapper


class ArmaniSpider(JaySpider):
    name = "diesel"
    item_xpath = ('//div[@class="packery"]//ul/li/a/@href',)
    page_xpath = ("//a/b/c",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
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
        item_loader.add_xpath("color", '//div/h5/span[@class="colorname"]/text()')
        item_loader.add_xpath("title", '//div[@class="product-discription clearfix "]/h2/text()')
        item_loader.add_xpath("image_urls", '//ul[@id="product-view"]/li/a/@data-href')
