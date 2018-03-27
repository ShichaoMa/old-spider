# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.ezcontacts_item import EzcontactsItem
from ..utils import CustomLoader, enrich_wrapper


class EzcontactsSpider(JaySpider):
    name = "ezcontacts"
    item_xpath = ('//div[@class="contact-info"]/../../a/@href',)
    page_xpath = ('//li[@class="next"]/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=EzcontactsItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//div[@class="product-content-header"]/h6/text()', re=r"ID:(\w+)")
        item_loader.add_re("product", r'CusDev.config = ({.*});')
        item_loader.add_xpath("list_price", '//*[@class="promo-price"]/text()')
        item_loader.add_xpath("price", '//*[@class="curr-price"]/text()')
        item_loader.add_xpath("title", '//h2[@class="product-name"]/text()')
