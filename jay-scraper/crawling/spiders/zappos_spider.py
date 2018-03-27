# -*- coding:utf-8 -*-
from toolkit import re_search

from . import JaySpider
from ..items.zappos_item import ZapposItem
from ..items.sixpm_item import SixpmItem
from ..utils import CustomLoader, enrich_wrapper


class ZapposSpider(JaySpider):
    name = "zappos"
    item_xpath = ('//*[@id="searchResults"]/a/@href',)
    page_xpath = ('//*[@id="resultWrap"]//div[@class="pagination"]/a[contains(text(),">")]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        if response.url.count("luxury"):
            return CustomLoader(item=ZapposItem())
        else:
            return CustomLoader(item=SixpmItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        if response.url.count("luxury"):

            item_loader.add_xpath("productId", '//input[@name="productId"]/@value')
            item_loader.add_value("productId", response.meta["url"], re=r"product/(\d+)")
            item_loader.add_value("product_id", "")
            item_loader.add_xpath("title", [
                '//*[@id="prdImage"]/h1/*//text()',
                '//*[@id="productStage"]/h1/*//text()',
                '//span[@itemprop="brand"]/parent::div//a/text()',
            ])
            item_loader.add_xpath("productDescription", '//div[@itemprop="description"]')
            item_loader.add_re("stockJSON", r'var stockJSON =([\S\s]+?);')
            item_loader.add_re("dimToUnitToValJSON", r'var dimToUnitToValJSON =([\S\s]+?);')
            item_loader.add_re("dimensions", r'var dimensions =([\S\s]+?);')
            item_loader.add_re("dimensionIdToNameJson", r'var dimensionIdToNameJson =([\S\s]+?);')
            item_loader.add_re("valueIdToNameJSON", r"var valueIdToNameJSON =\s?(.*);")
            item_loader.add_re("colorNames", r'var colorNames =([\S\s]+?);')
            item_loader.add_re("colorPrices", r'var colorPrices =([\S\s]+?);')
            item_loader.add_re("styleIds", r'var styleIds =([\S\s]+?);')
            item_loader.add_re("colorIds", r'var colorIds =([\S\s]+?);')
            item_loader.add_value("color_images", response.body)
            item_loader.add_value("image_urls", "")
            item_loader.add_value("availability", True)
        else:
            item_loader.add_xpath("product_id", '//meta[@name="branch:deeplink:product"]/@content')
            item_loader.add_value("product_id", response.request.url, re=r"product/(\d+)")
            item_loader.add_xpath("title", '//*[@class="vUkNo"]/span//text()')
            item_loader.add_xpath("productDescription", ['//div[@class="_1Srfn"]/ul', '//div[@class="_1Srfn _3Firw"]/ul'])
            item_loader.add_re("product_info", r"__INITIAL_STATE__ = ({.*});")
            item_loader.add_value("product", "")
            item_loader.add_value("color_images", "")
            item_loader.add_value("image_urls", "")

    def need_duplicate(self, url):
        return re_search(r"product/(\w+?)/", url)