# -*- coding:utf-8 -*-

from . import JaySpider
from ..utils import CustomLoader, enrich_wrapper
from ..items.farfetch_item import FarfetchItem


class FarfetchSpider(JaySpider):
    name = "farfetch"
    # 分类抓取的时候使用这两个属性
    item_xpath = ('//article/a/@href',)
    page_xpath = (r'(.*?)(page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (
                name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (
                name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=FarfetchItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath(
            "list_price", '//del[@data-tstid="priceInfo-original"]/text()')
        item_loader.add_xpath(
            "price", ['//strong[@data-tstid="priceInfo-original"]/text()',
                      '//strong[@data-tstid="priceInfo-onsale"]/text()'])
        item_loader.add_xpath("title", '//span[@itemprop="name"]/text()')
        item_loader.add_xpath(
            "features", '//div[@data-tstid="productDetails"]//p/text()')
        item_loader.add_xpath(
            "features", '//dl/*/text()', lambda values:
            [values[i] + values[i+1] + values[i+2] for i in range(0, len(values), 3)])
        item_loader.add_xpath(
            "sizes", '//select[@id="dropdown"]/option/following-sibling::option/text()')
        item_loader.add_re("image_urls", r'"large":"(.*?)"')
        item_loader.add_re("mpn", r'"designerStyleId":"(\w+)"')
        item_loader.add_re("model_number", r'"designerStyleId":"(\w+)"')
        item_loader.add_re("part_number", r'"designerStyleId":"(\w+)"')
        item_loader.add_re("product_id", r'"productId":(\d+)')

    def need_duplicate(self, url):
        return url