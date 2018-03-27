# -*- coding:utf-8 -*-
import os
import hashlib
from functools import reduce
from toolkit import safely_json_loads

from . import JaySpider
from ..items.coach_item import CoachBaseItem, CoachColorItem
from ..utils import enrich_wrapper, CustomLoader, ItemCollectorPath


class CoachSpider(JaySpider):
    name = "coach"
    # 商品详情页链接的xpath表达式或re表达式
    item_xpath = (
        "//h3/a/@href",
    )
    # 商品下一页的xpath表达式
    page_xpath = (
        "//a/b/c",
    )

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=CoachBaseItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_value("product_id", response.url, re="(\w+)\.html")
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("description", '//div[@class="pdp-info__description-content"]/p/text()')
        sub = item_loader.nested_css(".pdp-info__details ul")
        sub.add_xpath("features", "li/text()")
        item_loader.add_value("current_color", response.url)
        item_loader.add_re("image_urls", r"var s7jsonResponse = JSON.parse\('(.*?)'.replace")
        color_urls = response.xpath('//ul[@class="pdp-main__swatches swatch-list"]/li/a/@href').extract()
        for color_url in color_urls:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))] = CustomLoader(item=CoachColorItem())
        return [{"url": color_url,
                 "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))}} for color_url in color_urls]

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        self.logger.debug("Start to enrich prices. ")
        data = safely_json_loads(response.body)
        attrs = data["product"]["variationAttributes"]
        if len(attrs) > 1:
            item_loader.add_value("size", attrs[1])
        item_loader.add_value("color", reduce(lambda x, y: x if x["selected"] else y, attrs[0]["values"]))
        item_loader.add_value("sales_price", data["product"]["price"]["sales"]["formatted"])