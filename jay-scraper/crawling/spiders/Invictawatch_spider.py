# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.invictawatch_item import InvictawatchItem
from ..utils import CustomLoader, enrich_wrapper


class InvictawatchSpider(JaySpider):
    name = "invictawatch"
    item_xpath = ('//div[@class="row products"]/div/a/@href',)
    page_xpath = ('//a[@rel="next"]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=InvictawatchItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//meta[@itemprop="name"]/@content', re=r"(\d+)")
        item_loader.add_xpath("part_number", '//meta[@itemprop="name"]/@content', re=r"(\d+)")
        item_loader.add_xpath("description", '//meta[@itemprop="description"]/@content')
        item_loader.add_xpath("price", '//div[@class="pull-right price"]/text()', re=r"MSRP (.*)")
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("detail", '//div[@class="col-sm-6 col-xs-12 nopadding"]')
        item_loader.add_xpath("image_urls", '//div[@class="media-thumbs row"]/div/@data-src-l')
