# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.sixpm_item import SixpmItem
from .utils import re_search, CustomLoader, enrich_wrapper


class SixpmSpider(JaySpider):
    name = "6pm"
    item_xpath = ('//*[@id="searchResults"]/a/@href', )
    page_xpath = ('//*[@id="resultWrap"]//div[@class="pagination"]/a[contains(text(),">")]/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=SixpmItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//meta[@name="branch:deeplink:product"]/@content')
        item_loader.add_value("product_id", response.request.url, re=r"product/(\d+)")
        item_loader.add_xpath("title", '//div[@class="vUkNo"]/span/a/text()')
        item_loader.add_xpath("productDescription", ['//div[@class="_1Srfn"]', '//div[@class="_1Srfn _3Firw"]'])
        item_loader.add_re("product_info", r"__INITIAL_STATE__ = '(.*?)';")
        item_loader.add_value("product", "")
        item_loader.add_value("color_images", "")
        item_loader.add_value("image_urls", "")

    def need_duplicate(self, url):
        return re_search(r"product/(\w+?)/", url)