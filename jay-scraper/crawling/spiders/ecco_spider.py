# -*- coding:utf-8 -*-
import os
import hashlib
from toolkit import re_search

from . import JaySpider
from ..items.ecco_item import EccoItem, EccoColorItem
from ..utils import CustomLoader, enrich_wrapper, ItemCollectorPath, xpath_exchange


class EccoSpider(JaySpider):
    name = "ecco"
    item_xpath = ("//a[@class='name-link']/@href",)
    page_xpath = ('start=0',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=EccoItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_xpath("title", '//h1[@id="share-product-title"]/text()')
        product_id = re_search(r"(\d+)(?=\.html)", response.url)
        item_loader.add_value("product_id", product_id)
        item_loader.add_xpath("description", '//div[@class="desktop-DescriptionSection"]//div[@class="product-description detail-block"]/p/text()')
        item_loader.add_xpath("features", '//div[@class="desktop-DescriptionSection"]//div[@class="more-details"]/ul/li/text()')
        color_ids = set(url for url in response.xpath('//ul[@class="swatches Color"]/li/@id').extract())
        color_urls = ["https://us.shop.ecco.com/on/demandware.store/Sites-EccoUS-Site/default/Product-Variation?pid=%s&dwvar_%s_color=%s&Quantity=1&format=ajax"%(
            product_id, product_id, id.split("-")[-1]) for id in color_ids]
        for color_url in color_urls:
                response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                    str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                        color_url.encode("utf-8")).hexdigest()))] = CustomLoader(item=EccoColorItem())
        return [{"url": color_url,
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                         color_url.encode("utf-8")).hexdigest()))}} for color_url in color_urls]

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        self.logger.debug("Start to enrich colors. ")
        item_loader.add_xpath("image_urls", '//ul[@class="autoplay slider"]/li/a/img/@src')
        item_loader.add_xpath("color", '//div[@class="selectedColor"]/span/span[@class="color-name"]/text()')
        item_loader.add_value("color_id", re_search(r"_color=(\d+)", response.url))
        item_loader.add_xpath("standard_price", ['//span[@class="price-standard new-product-style"]/text()',
                              '//span[@class="product-price-normal new-product-style"]/text()'])
        item_loader.add_xpath("sales_price", ['//span[@class="price-sales new-product-style"]/text()',
                                              '//div[@class="product-price"]/text()'])
        sizes = [(xpath_exchange(size.xpath("a/span/text()")), xpath_exchange(size.xpath("a/div/text()")))
                 for size in response.xpath('//div[@id="tabUS"]/ul[@class="swatches size sizepanel"]/li')]
        item_loader.add_value("sizes", sizes)
