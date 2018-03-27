# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.casio_item import CasioItem
from .utils import CustomLoader, enrich_wrapper


class CasioSpider(JaySpider):
    name = "casio"
    item_xpath = ('//div[@class="model-list grid-2 grid--4"]/div/div/a/@href',)
    page_xpath = ("//a/b/c",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=CasioItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//div[@class="name"]/h2/text()')
        item_loader.add_xpath("part_number", '//div[@class="name"]/h2/text()')#, '//div[@class="style-number-title"]/span/text()')
        item_loader.add_xpath("price", '//div[@class="price t-size-large"]/span/text()')
        item_loader.add_xpath("feature", '//figure/text()')
        item_loader.add_xpath("title", '//div[@class="name"]/h2/text()')
        item_loader.add_xpath("specification", '//ul[@class="display-list"]')
        item_loader.add_xpath("description", '//div[@class="js-cont-wrap"]/p')
        item_loader.add_xpath("image_urls", '//meta[@property="og:image"]/@content')
