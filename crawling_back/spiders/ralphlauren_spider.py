# -*- coding:utf-8 -*
import os
import re
from urllib.parse import urlencode

from . import JaySpider
from .utils import enrich_wrapper, CustomLoader, ItemCollectorPath, re_search
from ..items.ralphlauren_item import RalphlaurenItem, RalphlaurenSkuItem


class RalphlaurenSpider(JaySpider):
    name = "ralphlauren"
    item_xpath = (
        '//li[@id]/div[@class="product-photo"]/div/a/@href',
        '//div[@class="product-image"]/a[@class="thumb-link"]/@href'
    )
    page_xpath = (
        '//div[@id="grid-nav-bottom"]/div/a[@class="results next-page"]/@href',
        '//a[@class="page-next"]/@href',
    )

    custom_settings = {
        "ITEM_PIPELINES": {
        'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=RalphlaurenItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_re("product_id", r"id: '(\d+)',")
        item_loader.add_xpath("product_name", '//h1/text()')
        colors = response.css(".colorname .swatchanchor img").xpath("@alt").extract()
        sizes = response.css(".primarysize .swatchanchor").xpath("text()").extract()
        skus = [(color.strip().replace("/", "***"), size.strip().replace("/", "***")) for color in colors for size in sizes if size.strip()]
        req_dict = list()
        pid = re_search(r"id: '(\d+)',", response.body)
        for sku in skus:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "skus#%s_%s" % sku))] = CustomLoader(item=RalphlaurenSkuItem())
            params = {
                "pid": pid,
                "dwvar_%s_primarysize"%pid: sku[1].replace("***", "/"),
                "dwvar_%s_colorname"%pid: sku[0].replace("***", "/"),
                "Quantity":1,
                "format": "ajax"
            }
            req_dict.append(
            {"url": "https://www.ralphlauren.com/on/demandware.store/Sites-RalphLauren_US-Site/default/Product-Variation?" + urlencode(params),
             "meta": {"path": ItemCollectorPath(os.path.join(str(response.meta["path"]), "skus#%s_%s" % sku))}})
        image_set_url = "".join(response.selector.re(r'var set = "(.*?)";'))
        swatches = response.selector.re(r"swatch_(\d+)")
        params = {
            "req": "set,json,UTF-8",
            "labelkey": "label",
            "id": 66532471, # 这个参数不知道是从哪里取的，不写还不行，写死可以，虽然写的是另一个商品的
            "handler": "s7classics7sdkJSONResponse",
        }
        for swatch in swatches:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "image_urls#%s" % swatch))] = item_loader
            req_dict.append({"url": re.sub(r"(?<=s7-)\d+", swatch, image_set_url) + "?" + urlencode(params),
                "meta": {"path": ItemCollectorPath(os.path.join(str(response.meta["path"]), "image_urls#%s" % swatch))}})
        item_loader.add_xpath("detail", '//div[@class="product-details-section"]')
        item_loader.add_value("color_images", "")
        return req_dict

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        item_loader.add_xpath("price", ['//span[@class="price-sales no-promotion"]/text()',
                                        '//span[@class="price-sales"]/text()'])
        item_loader.add_xpath("standard_price", '//span[@class="price-standard"]/text()')
        item_loader.add_xpath('id', '//input[@id="pid"]/@value')
        item_loader.nested_css(".primarysize .selected a").add_xpath("size", "text()")
        color_loader = item_loader.nested_css(".colorname  .selected a > img")
        color_loader.add_xpath("color", "@alt")
        color_loader.add_xpath("color_id", "@src", re=r"swatch_(\d+)")
        item_loader.add_xpath("status", '//p[@class="in-stock-msg"]/text()')
        item_loader.add_value("is_available", "")

    @enrich_wrapper
    def enrich_image_urls(self, item_loader, response):
        self.logger.debug("Start to enrich image_urls. ")
        item_loader.add_re("image_urls", r"s7classics7sdkJSONResponse\((.*),\"66532471\"\);")

    def need_duplicate(self, url):
        return url