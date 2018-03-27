# -*- coding:utf-8 -*
from . import JaySpider
from .utils import enrich_wrapper, CustomLoader
from ..items.victoriassecret_item import VictoriassecretItem


class VictoriassecretSpider(JaySpider):
    name = "victoriassecret"
    item_xpath = ('//li/a[@class="ssf3"]/@href', '//li/div/a[@class="ssf3"]/@href')
    page_xpath = ('//a/b/c',)

    custom_settings = {
        "ITEM_PIPELINES": {
        'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=VictoriassecretItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("utag_data", r'var utag_data = ({.*?);')
        item_loader.add_value("product_id", "")
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("description", '//div[@class="long-description"]')
        item_loader.add_value("product_assetId", '')
        item_loader.add_re("all_skus", r'"pagedata.itemPrice", (\[[\s\S]*?\])\);')
        item_loader.add_value("skus", '')
        item_loader.add_re("selectors", r'"pagedata.selectors", ({[\s\S]*?})\);')
        item_loader.add_re("atpdata", r'"pagedata.atp", ({.*})\);')
        item_loader.add_xpath("item_number", '//p[@class="itemNbr"]/text()')
        item_loader.add_re("product_images", r'"pagedata.altImages", ({[\s\S]*?})\);')
        item_loader.add_value("color_images", "")
        item_loader.add_value("image_urls", "")
