# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.citizen_item import CitizenItem
from .utils import CustomLoader, enrich_wrapper


class CitizenSpider(JaySpider):
    name = "citizen"
    item_xpath = ('//li[@class="column"]/div/a/@href',)
    page_xpath = ('//a/b/c',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=CitizenItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//p[@class="product_pdNumber"]/text()')
        item_loader.add_xpath("part_number", '//p[@class="product_pdNumber"]/text()')
        item_loader.add_xpath("price", '//p[@class="product_pdPrice"]/text()')
        item_loader.add_xpath("description", '//meta[@name="description"]/@content')
        item_loader.add_xpath("title", '//title/text()')
        item_loader.add_xpath("detail", '//div[@class="featureDetailWrap clearfix"]')
        item_loader.add_xpath("image_urls", '//img/@data-large')
