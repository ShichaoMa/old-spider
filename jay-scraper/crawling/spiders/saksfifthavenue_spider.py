# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.saksfifthavenue_item import SaksfifthavenueItem
from ..utils import CustomLoader, enrich_wrapper


class SaksfifthavenueSpider(JaySpider):
    name = "saksfifthavenue"
    item_xpath = ('//div[@class="product-text"]/a/@href',)
    page_xpath = ('//li[@class="pa-enh-pagination-right-arrow"]/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
        "COOKIES": "E4X_CURRENCY=USD;E4X_COUNTRY=US;"
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=SaksfifthavenueItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("product_id", r'"productCode":"(\d+)"')
        item_loader.add_xpath("title", '//h1[@class="product-overview__short-description"]/text()')
        item_loader.add_xpath("features", '//*[@class="product-description"]/div/ul/li/text()')
        item_loader.add_xpath("color", '//dd[@class="product-variant-attribute-label__selected-value"]/text()')
        size_name = response.xpath('//ul[@class="product-variant-attribute-values"]/li/span/text()').extract()
        size_id = response.xpath('//ul[@class="product-variant-attribute-values"]/li/span/@data-reactid').extract()
        size_aval = response.xpath('//ul[@class="product-variant-attribute-values"]/li/@class').extract()
        item_loader.add_value("sizes", zip(size_id, size_name, size_aval))
        item_loader.add_xpath("price", '//dd[@class="product-pricing__price"]/span[@itemprop="price"]/text()')
        item_loader.add_re("image_server_url", r'"images_server_url":"(.*?)"')
        item_loader.add_re("images_path",  r'"images_path":"(.*?)"')
        item_loader.add_re("image_urls", r'"images":(.*?\])')
