# -*- coding:utf-8 -*
import os

from functools import partial
from toolkit import safely_json_loads

from . import JaySpider
from ..utils import enrich_wrapper, CustomLoader, xpath_exchange, ItemCollectorPath
from ..items.ninewest_item import NinewestItem


class NinewestSpider(JaySpider):
    name = "ninewest"
    item_xpath = ('//div[@class="contentProduct"]/div/div/a/@href',)
    page_xpath = ('start=0',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=NinewestItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        product_id = xpath_exchange(response.xpath('//input[@id="productID"]/@value'))
        item_loader.add_value("product_id", product_id)
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("description", '//div[@class="descContent"]/text()')
        item_loader.add_xpath("features", '//div[@class="detailItem"]/text()')
        color_ids = response.xpath('//span[@class="colorChipWrapper"]/img/@option-value').extract()
        item_loader.add_xpath("colors", '//span[@class="colorChipWrapper"]/img/@title', partial(zip, color_ids))
        color_url_tmpl = "http://www.ninewest.com/on/demandware.store/Sites-ninewest-Site/default/FluidProduct-GetProductAvailability?pid=%s&color=%s&returnObject=ProductMaster,VariationProducts"
        for color_id in color_ids:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "skus#%s"%color_id))] = item_loader
        return [{"url": color_url_tmpl%(product_id, color_id), "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "skus#%s" % color_id))}} for color_id in color_ids]

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        color_meta = safely_json_loads(response.body)["response"]["productMaster"]
        item_loader.add_value("skus", color_meta["variationProducts"])
        images = list()
        for typ, image_url in color_meta["defaultImage"].items():
            if typ.count("Zoom") and image_url:
                images.append({"type": typ, "url": image_url})
        item_loader.add_value("color_images", {color_meta["defaultColorCode"]: images})
