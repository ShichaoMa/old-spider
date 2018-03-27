# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.certifiedwatchstore_item import CertifiedwatchstoreItem
from ..utils import CustomLoader, enrich_wrapper


class CertifiedwatchstoreSpider(JaySpider):
    name = "certifiedwatchstore"
    item_xpath = (
        '//div[@class="category-products"]/ul/li/div[not(span)]/a/@href',
        '//div[@class="category-products"]/ul/li/div/a/@href',
    )
    page_xpath = ('//a[@class="next i-next"]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=CertifiedwatchstoreItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath('title', '//h1/text()')
        item_loader.add_xpath('product_id', '//span[@itemprop="sku"]/text()')
        item_loader.add_xpath('model_number', '//p[@class="itemDes"]/text()', re=r"Model:\s*(\S+)")
        item_loader.add_xpath('part_number', '//p[@class="itemDes"]/text()', re=r"Model:\s*(\S+)")
        item_loader.add_xpath('mpn', '//p[@class="itemDes"]/text()', re=r"Model:\s*(\S+)")
        item_loader.add_xpath('special_price', '//p[@class="special-price"]/span[@class="price"]/text()')
        item_loader.add_xpath('msr_price', '//p[@class="msrPri"]/span[@class="price"]/text()')
        sub_loader = item_loader.nested_css('.availability > span')
        sub_loader.add_xpath('availability_reason', "text()")
        item_loader.add_value("availability", "")
        item_loader.add_value("stock", "")
        item_loader.add_xpath('description', '//p[@itemprop="description"]/..')
        item_loader.add_xpath('upc', '//strong[contains(text(), "UPC")]/../../td[2]/text()')
        item_loader.add_xpath('image_urls', [
            '//a[@class="MagicZoom"]/@href',
            '//*[@data-magic-slide-id="zoom"]/@href',
        ])