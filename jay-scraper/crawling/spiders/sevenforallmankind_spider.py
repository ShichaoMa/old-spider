# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.sevenforallmankind_item import SevenforallmankindItem
from ..utils import CustomLoader, enrich_wrapper


class SevenforallmankindSpider(JaySpider):
    name = "7forallmankind"
    page_xpath = (r'(.*?)(Page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    def extract_item_urls(self, response):
        return [response.urljoin(x) for x in set(response.selector.re(r'"DetailsUrl":"(.*?)"'))]

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=SevenforallmankindItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("pagedata", r"var __onestop_pageData\s*=\s*(\{.*?\});")
        item_loader.add_value("title", "")
        item_loader.add_value("product_id", "")
        item_loader.add_value("sku", "")
        item_loader.add_value("colors", "")
        item_loader.add_value("size", "")
        item_loader.add_value("description", "")
        item_loader.add_value("features", "")
        item_loader.add_value("color_images", "")
        item_loader.add_re("image_urls", r"\"ImageUrl\":\"//(s\S*?\.jpg)\"")
