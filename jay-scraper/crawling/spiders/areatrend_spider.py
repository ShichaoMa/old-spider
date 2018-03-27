# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.areatrend_item import AreatrendItem
from ..utils import CustomLoader, enrich_wrapper, extract_specs


class AreatrendSpider(JaySpider):
    name = "areatrend"
    item_xpath = ('//div[@class="product-item-info"]/div/a/@href',)
    page_xpath = (r'(.*?)(p=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
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
        self.logger.debug("Start to enrich data. ")
        item_loader.add_xpath("product_id", '//div[@class="product attribute sku"]/div[@class="value"]/text()')
        item_loader.add_xpath("model_number", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("part_number", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("mpn", '//td[@data-th="Style"]/text()')
        item_loader.add_xpath("title", '//h1[@class="page-title"]/span/text()')
        item_loader.add_re("skus", r'"jsonConfig": ({.+}),')
        item_loader.add_xpath("old_price", ['//span[@class="old-price"]//span[@class="price"]/text()',
                                            '//div[@class="product-info-price"]//span[@class="price"]/text()'])
        item_loader.add_xpath("special_price", '//span[@class="special-price"]//span[@class="price"]/text()')
        item_loader.add_re("color_size", r'"jsonSwatchConfig": ({.+}),')
        item_loader.add_xpath("features", '//div[@class="value"]/ul/li/text()')
        item_loader.add_re("color_images", r'"data": (\[[\S\s]+?\]),')
        item_loader.add_xpath("description", '//div[@class="product attribute description"]/div/text()')
        item_loader.add_xpath("detail", '//div[@id="additional"]')
        item_loader.add_value("specs", extract_specs(response.selector, '//table[@id="product-attribute-specs-table"]//tr'))
        item_loader.add_value("availability", True)

    def need_duplicate(self, url):
        return url