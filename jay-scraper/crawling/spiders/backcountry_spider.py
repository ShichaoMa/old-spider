# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.backcountry_item import BackcountryItem
from ..utils import CustomLoader, enrich_wrapper, xpath_exchange


class BackcountrySpider(JaySpider):
    name = "backcountry"
    item_xpath = (
        '//div[@class="contentBody pageUp"]/div/table/tbody/tr/td/a/@href',
        '//div[@class="product ui-product-listing js-product-listing product-swatches js-product-swatches"]/a/@href',
        '//section[@class="plp-main plp-container"]/div/div/a/@href',
        '//section[@class="plp-main plp-container"]/div/div/div/a/@href',
    )
    page_xpath = ('//li[@class="pag-next"]/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
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
        sub = item_loader.nested_css(".product-details-accordion__description")
        sub.add_xpath("description", "p/text()")

        item_loader.add_xpath("features", '//ul[@class="product-details-accordion__list"]/li/text()')
        specs = [[xpath_exchange(tr.xpath("div[1]/text()")), xpath_exchange(tr.xpath("div[2]/text()"))]
                 for tr in response.css(".product-details-accordion__techspecs-container > div")]
        item_loader.add_value("specs", specs)
