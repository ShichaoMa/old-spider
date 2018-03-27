# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.jacobtime_item import JacobtimeItem
from ..utils import CustomLoader, enrich_wrapper, xpath_exchange


class JacobtimeSpider(JaySpider):
    name = "jacobtime"
    item_xpath = ('//div[@class="product__image"]/a/@href',)
    page_xpath = ('//a[@title=" Next Page "]/@href', '//span[@class="jcf-select-opener page-next"]/../../a/@href')

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
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
                '//header[@class="product-information__head"]/h4/text()',
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
            "retail", ['//span/del/text()',
                       '//span[@class="text-linethrough"]/text()'])
        item_loader.add_xpath("your_price", [
                '//div[@class="product-price"]/strong/text()',
                '//span[@class="productSpecialPriceLarge"]/text()',
                '//span[@class="text-linethrough"]/parent::h2/text()',
            ])
        item_loader.add_xpath("features", '//ul[@class="feature-details"]/li/text()')
        specs = [[xpath_exchange(tr.xpath("td[1]//text()")), xpath_exchange(tr.xpath("td[2]//text()"))]
                 for tr in response.xpath('//table[@class="table-details"]//tr')]
        item_loader.add_value("specs", specs)
        item_loader.add_xpath("image_urls", '//div[@class="slider__slide"]/a/@href')
        item_loader.add_xpath("upc_or_ean", '//td[contains(text(), "UPC")]/following-sibling::td/span/text()')
        item_loader.add_xpath("availability", '//a[@id="add_to_notify"]')
        item_loader.add_xpath("availability_reason", ['//div[@class="product__actions"]/p/span/span/text()',
                                                      '//p[@class="stock_message"]/text()',
                                                      '//a[@id="add_to_notify"]/../h2/text()'])
