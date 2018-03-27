# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.gucci_item import GucciItem
from ..utils import CustomLoader, enrich_wrapper


class GucciSpider(JaySpider):
    name = "gucci"
    item_xpath = ('//a[@class="product-tiles-grid-item-link"]/@href',)
    page_xpath = ("0~=(/)(\d+)()",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=GucciItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_value("product_id", response.url, re=r"p-(\w+)")
        item_loader.add_value("part_number", response.url, re=r"p-(\w+)")#, '//div[@class="style-number-title"]/span/text()')
        item_loader.add_xpath("price", '//span[@id="markedDown_full_Price"]/text()')
        item_loader.add_xpath("color", '//span[@class="color-material-name"]/text()')
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("detail", '//div[@class="accordion-drawer"]')
        item_loader.add_xpath("image_urls", '//img[@class="zoom-img"]/@src')
