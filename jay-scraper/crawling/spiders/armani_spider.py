# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.armani_item import ArmaniItem
from ..utils import CustomLoader, enrich_wrapper


class ArmaniSpider(JaySpider):
    name = "armani"
    item_xpath = ('//a[@class="url"]/@href',)
    page_xpath = ("//a/b/c",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=ArmaniItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_value("product_id", response.url, re=r"_(\w+)")
        item_loader.add_xpath("part_number", '//span[@class="MFC"]/text()')
        item_loader.add_xpath("price", '//span[@class="priceValue"]/text()')
        item_loader.add_xpath("color", '//ul[@class="Colors"]/li/a/text()')
        item_loader.add_xpath("size", '//ul[@class="SizeW"]/li/a/text()')
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("detail", '//ul[@class="descriptionList"]')
        item_loader.add_xpath("image_urls", '//div[@class="thumbElement"]/img/@src')
