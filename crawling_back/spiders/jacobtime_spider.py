# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.jacobtime_item import JacobtimeItem
from .utils import CustomLoader, enrich_wrapper


class JacobtimeSpider(JaySpider):
    name = "jacobtime"
    item_xpath = ('//div[@class="col"]/article[@class="product-col"]/a[div]/@href',)
    page_xpath = ('//a[@title=" Next Page "]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
            'crawling.spidermiddlewares.InfluxDBMiddleware': 990,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=JacobtimeItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("brand", '//h1/text()')
        item_loader.add_xpath("descript_title", [
                '//span[@class="descript-title"]/text()',
                '//h1[@class="descript-title"]/text()',
                "//header/p/text()"
            ])
        item_loader.add_re("products_id", r"var sa_product = '(.*?)'; ")
        item_loader.add_re("model_number", r"var sa_product = '(.*?)'; ")
        item_loader.add_re("mpn", r"var sa_product = '(.*?)'; ")
        item_loader.add_re("part_number", r"var sa_product = '(.*?)'; ")
        item_loader.add_value("product_id", "")
        item_loader.add_xpath(
            "retail", '//span[@class="text-linethrough"]/text()')
        item_loader.add_xpath("your_price", [
                '//span[@class="productSpecialPriceLarge"]/text()',
                '//span[@class="text-linethrough"]/parent::h2/text()',
            ])
        item_loader.add_xpath("details", '//section[@id="tab01"]')
        item_loader.add_xpath("image_urls", '//div[@class="img-holder"]/a/@href')
        item_loader.add_xpath("upc_or_ean", '//td[contains(text(), "UPC")]/following-sibling::td/span/text()')