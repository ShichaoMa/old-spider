# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.areatrend_item import AreatrendItem
from .utils import CustomLoader, enrich_wrapper


class AreatrendSpider(JaySpider):
    name = "areatrend"
    item_xpath = ('//div[@class="product-item-info"]/div/a/@href',)
    page_xpath = (r'(.*?)(p=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
            'crawling.spidermiddlewares.InfluxDBMiddleware': 990,
            'crawling.spidermiddlewares.AreatrendMiddleware': 991,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=AreatrendItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//div[@class="product attribute sku"]/div[@class="value"]/text()')
        item_loader.add_xpath("model_number", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("part_number", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("mpn", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("title", '//h1[@class="page-title"]/span/text()')
        item_loader.add_re("skus", r'"jsonConfig": ({[\s\S]+?}}}),')
        item_loader.add_xpath("old_price", ['//span[@class="old-price"]//span[@class="price"]/text()',
                                            '//div[@class="product-info-price"]//span[@class="price"]/text()'])
        item_loader.add_xpath("special_price", '//span[@class="special-price"]//span[@class="price"]/text()')
        item_loader.add_re("color_size", r'"jsonSwatchConfig": ({[\s\S]+?}}}),')
        item_loader.add_xpath("feature", '//div[@class="value"]/ul')
        item_loader.add_value("color_images", "")
        item_loader.add_xpath("description", '//div[@class="product attribute description"]')
        item_loader.add_xpath("detail", '//div[@id="additional"]')
        item_loader.add_xpath("spec", '//table[@id="product-attribute-specs-table"]')
        item_loader.add_re("image_urls", r'"data": (\[[\S\s]+?\]),')
        item_loader.add_value("availability", True)

    def need_duplicate(self, url):
        return url