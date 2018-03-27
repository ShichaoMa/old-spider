# -*- coding:utf-8 -*-
import os
import time

from . import JaySpider
from ..items.newegg_item import NeweggItem, NeweggSkuItem
from ..utils import CustomLoader, enrich_wrapper, extract_specs, ItemCollectorPath, xpath_exchange


class NeweggSpider(JaySpider):
    name = "newegg"
    item_xpath = ('//a[@class="item-title"]/@href',)
    page_xpath = (r'(.*?)(Page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=NeweggItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_xpath("product_id", '//input[@id="hiddenItemGroupId"]/@value')
        item_loader.add_re("product_info", r"ProductProperty = ({.*?});")
        build_urls = response.selector.re(r'"itemNumber4BuildUrl":"(\w+)"')
        if build_urls:
            for sku_url in build_urls:
                response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                    str(response.meta["path"]), "skus#%s" % sku_url))] = CustomLoader(item=NeweggSkuItem())
            return [{"url": "https://www.newegg.com/Product/Product.aspx?item=%s"%sku_url,
                     "meta": {"path": ItemCollectorPath(os.path.join(
                         str(response.meta["path"]), "skus#%s" % sku_url))}} for sku_url in build_urls]
        else:
            self.enrich_skus(item_loader, response)

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        item_loader.add_re("sku_id", r"product_id:\['(.*?)']")
        item_loader.add_xpath("title", '//h1[@id="grpDescrip_h"]/span/text()')
        item_loader.add_re("model_number", r"product_model:\['(.*?)'\],")
        item_loader.add_re("part_number", r"product_model:\['(.*?)'\],")
        item_loader.add_re("mpn", r"product_model:\['(.*?)'\],")
        item_loader.add_xpath("price", '//div/meta[@itemprop="price"]/@content')
        item_loader.add_xpath("list_price", '//li[@class="price-was"]/text()')
        size_width = xpath_exchange(response.xpath('//dt[contains(text(), "Size")]/following-sibling::dd/text()')).split(" ")
        item_loader.add_xpath("width", '//dt[contains(text(), "Width")]/following-sibling::dd/text()')
        if len(size_width) > 1:
            size, width = size_width
            item_loader.add_value("width", width)
        else:
            size = size_width
        item_loader.add_value("size", size)
        item_loader.add_re("size_id", '"name":36014,"value":(\d+)')
        item_loader.add_xpath("color", '//dt[contains(text(), "Color")]/following-sibling::dd/text()')
        item_loader.add_re("color_id", '"name":35932,"value":(\d+)')
        item_loader.add_re("stock", r"product_instock:\['(.*?)'\]")
        item_loader.add_xpath("description", '//div[@class="itemDesc"]/p/text()')
        specs = extract_specs(response.selector, '//div[@id="Specs"]/fieldset/dl', ".//text()")
        item_loader.add_value("specs", specs)
        item_loader.add_re("image_urls", r'"imageNameList":"(.*?)"')
        item_loader.add_value("url", response.url)
        item_loader.add_value("timestamp", time.time())