# -*- coding:utf-8 -*-
from urllib.parse import urlparse, urlunparse, urlencode

from . import JaySpider
from ..items.watchstation_item import WatchstationItem
from .utils import CustomLoader, enrich_wrapper, url_item_arg_increment, urldecode, TakeFirst


class WatchstationSpider(JaySpider):
    name = "watchstation"
    item_xpath = ('//div[@class="prodName"]/a/@href',)
    path = "/webapp/wcs/stores/servlet/FSAJAXService"
    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
            'crawling.spidermiddlewares.InfluxDBMiddleware': 990,
        }
    }

    def extract_page_urls(self, response, effective_urls, item_urls):
        if response.xpath('//div[@class="pagination"]'):

            if response.xpath('//div[@class="pagination"]/a[contains(text(), "Next")]'):
                url = url_item_arg_increment("No=0", response.url, 20)
                #parts = urlparse(url)
            else:
                return None
        else:
            #parts = urlparse(response.url)
            url = "".join(response.selector.re(r"var productServiceURL = \"(.*)\";"))
        # query = urldecode(parts.query)
        # query["service"] = "getProductList"
        # query.setdefault("No", 0)
        # parts = parts._replace(path=self.path, query=urlencode(query))
        # url = urlunparse(parts)
        response.meta["if_next_page"] = True
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        return [url]

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=WatchstationItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("title", '//h1[@class="pdpBrandTitle"]/a/text()')
        item_loader.add_re("product_id", r'"productId":(\d+)')
        item_loader.add_xpath("part_number", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("mpn", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("model_number", '//div[@class="sku"]/text()', re=r"Style #:(\S+)")
        item_loader.add_xpath("old_price", '//div[@id="priceDetails"]/span[@class="strike"]/text()')
        item_loader.add_xpath("price", ['//div[@id="priceDetails"]/span[@class="newPrice"]/text()',
                                        '//span[@class="price"]/text()'])
        item_loader.add_xpath("feature", '//div[@class="productSpecs"]')
        item_loader.add_xpath("description", '//div[@class="productDescription"]')
        item_loader.add_xpath("image_urls", '//meta[@property="og:image"]/@content', TakeFirst())
