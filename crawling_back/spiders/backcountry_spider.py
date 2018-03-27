# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.backcountry_item import BackcountryItem
from .utils import CustomLoader, enrich_wrapper


class BackcountrySpider(JaySpider):
    name = "backcountry"
    item_xpath = (
        '//div[@class="contentBody pageUp"]/div/table/tbody/tr/td/a/@href',
        '//div[@class="product ui-product-listing js-product-listing product-swatches js-product-swatches"]/a/@href',
        '//section[@class="plp-main plp-container"]/div/div/a/@href',
    )
    page_xpath = ('//li[@class="pag-next"]/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=BackcountryItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_re("products", "BC.product = (.*?);")
        item_loader.add_value("sku", response.meta["url"], re=r"skid=(\w+)")
        item_loader.add_value("product_id", "")
        item_loader.add_xpath("title", '//title/text()')
        item_loader.add_value("skus_collection", "")
        item_loader.add_xpath("image_urls", '//div[@class="product-media-main"]'
                                            '//ul/li/div[@class="ui-flexzoom js-flexzoom"]/@data-zoom')
        item_loader.add_value("color_images", "")
        item_loader.add_xpath("description1", '//div[@class="product-details-accordion__description '
                                           'js-product-description js-buybox-details-long-description"]')
        item_loader.add_xpath("description2", '//ul[@class="product-details-accordion__list"]')
        item_loader.add_xpath("details", '//div[@class="product-details-accordion__container"]')
