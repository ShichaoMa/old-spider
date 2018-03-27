# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.jomashop_item import JomashopItem
from .utils import re_search, CustomLoader, enrich_wrapper


class JomashopSpider(JaySpider):
    name = "jomashop"
    item_xpath = ('//ul[@class="products-grid"]/li/div[not(p)]/a[@class="product-image"]/@href',)
    page_xpath = (r'(.*?)(p=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=JomashopItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("brand_name", '//form[@id="product_addtocart_form"]//span[@class="brand-name"]/text()')
        item_loader.add_xpath("product_name", '//form[@id="product_addtocart_form"]//span[@class="product-name"]/text()')
        item_loader.add_re("product_ids", r'"sku": "(.+?)"')
        item_loader.add_xpath("model_number", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_xpath("mpn", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_xpath("part_number", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_value("product_id", "")
        item_loader.add_xpath("final_price",
                              '//*[@id="product_addtocart_form"]//p[@class="final-price"]'
                              '/meta[@itemprop="price"]/@content')
        item_loader.add_xpath("retail_price",
                              '//*[@id="product_addtocart_form"]//li[@class="pdp-retail-price"]/span/text()')
        item_loader.add_xpath("savings", '//*[@id="product_addtocart_form"]//li[@class="pdp-savings"]/span/text()')
        item_loader.add_xpath("shipping", [
            '//*[@id="product_addtocart_form"]//li[@class="pdp-shipping"]/span/text()',
            '//span[@class="pdp-shipping-availability"]/span/span[@class="instock-ready"]/text()',
        ], re=r"(\$?[\d\.]*)")
        item_loader.add_xpath("shipping_availability", [
            '//span[@class="pdp-shipping-availability"]/span/span[@class="instock"]/text()',
            '//span[@class="large-availability"]/text()',
        ])
        item_loader.add_xpath("image_value", '//input[@name="product"]/@value')
        item_loader.add_value("image_urls", response.body)
        item_loader.add_xpath("details", '//dd[@id="tab-container-details"]')
        item_loader.add_xpath("Color", [
            '//span[@id="Dial Color"]/text()',
            '//span[@id="Color"]/text()',
        ])
        item_loader.add_xpath("upc", '//span[@id="UPC Code"]/text()')
