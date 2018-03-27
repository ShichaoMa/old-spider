# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.joesnewbalanceoutlet_item import JoesnewbalanceoutletiItem
from .utils import CustomLoader, enrich_wrapper


class JoesnewbalanceoutletSpider(JaySpider):
    name = "joesnewbalanceoutlet"
    item_xpath = ('//a[@class="impression"]/@href',)
    page_xpath = (r'(.*?)(Page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=JoesnewbalanceoutletiItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id", r'resx.itemid = "(.*?)"')
        item_loader.add_re("price", r"'price': '(.*?)',")
        item_loader.add_xpath("color", '//span[@id="Sku"]/text()')
        item_loader.add_xpath("description", '//div[@id="Description"]')
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("detail", '//div[@class="hideOnMobile"]/div/ul[@class="productFeaturesDetails"]')
        item_loader.add_re("skus", r' variants: (\[.*?\]),')
        item_loader.add_re("children", r' children: (\[.*?\]),')
        item_loader.add_xpath("image_urls", '//a[@class="fancybox"]/@href')
