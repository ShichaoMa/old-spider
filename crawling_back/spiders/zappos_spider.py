# -*- coding:utf-8 -*-
from .sixpm_spider import SixpmSpider
from ..items.zappos_item import ZapposItem
from .utils import CustomLoader, enrich_wrapper


class ZapposSpider(SixpmSpider):
    name = "zappos"
    # item_xpath = ('//*[@id="searchResults"]/a/@href', )
    # page_xpath = ('//*[@id="resultWrap"]//div[@class="pagination"]/a[contains(text(),"»")]/@href',)
    #
    # custom_settings = {
    #     "ITEM_PIPELINES": {
    #         'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
    #     },
    # }

    @staticmethod
    def get_base_loader(response):
        if response.url.count("luxury"):
            return CustomLoader(item=ZapposItem())
        else:
            return SixpmSpider.get_base_loader(response)

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
            item_loader.add_xpath("productDescription", [
                '//div[@id="prdInfoText"]',
                '//div[@id="productDescription"]',
                '//div[@itemprop="description"]',
            ])
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
            super(ZapposSpider, self).enrich_data(item_loader, response)
    #
    # def need_duplicate(self, url):
    #     return re_search(r"product/(\w+?)/", url)