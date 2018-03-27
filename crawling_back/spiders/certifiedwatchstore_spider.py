# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.certifiedwatchstore_item import CertifiedwatchstoreItem
from .utils import CustomLoader, enrich_wrapper


class CertifiedwatchstoreSpider(JaySpider):
    name = "certifiedwatchstore"
    item_xpath = (
        '//div[@class="category-products"]/ul/li/div[not(span)]/a/@href',
        '//div[@class="category-products"]/ul/li/div/span[not(contains(text(), "Notify"))]/../a/@href',
    )
    page_xpath = ('//a[@class="next i-next"]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=CertifiedwatchstoreItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath('title', '//h1/text()')
        item_loader.add_xpath('product_id', '//span[@itemprop="sku"]/text()')
        item_loader.add_xpath('model_number', '//p[@class="itemDes"]/text()', re=r"Model: (\S+)")
        item_loader.add_xpath('part_number', '//p[@class="itemDes"]/text()', re=r"Model: (\S+)")
        item_loader.add_xpath('mpn', '//p[@class="itemDes"]/text()', re=r"Model: (\S+)")
        item_loader.add_xpath('special_price', '//p[@class="special-price"]/span[@class="price"]/text()')
        item_loader.add_xpath('msr_price', '//p[@class="msrPri"]/span[@class="price"]/text()')
        item_loader.add_xpath('availability_reason', '//div[@class="product-main-info"]/p/text()')
        item_loader.add_xpath('description', '//p[@itemprop="description"]/..')
        item_loader.add_xpath('upc', '//strong[contains(text(), "UPC")]/../../td[2]/text()')
        item_loader.add_xpath('image_urls', [
            '//*[@data-magic-slide-id="zoom"]/@href',
            '//a[@class="MagicZoom"]/@href',
        ])