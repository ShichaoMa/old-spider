# -*- coding:utf-8 -*-
import re
import json

from urllib.parse import unquote, urlencode

from . import JaySpider
from ..items.swarovski_item import SwarovskiItem
from ..utils import CustomLoader, enrich_wrapper


class SwarovskSpider(JaySpider):
    name = "swarovski"
    item_xpath = ('//div[@class="listproduct"]/p/a/@href',)
    url = "http://www.swarovski.com/Web_US/en/json/json-result"
    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
            'crawling.spidermiddlewares.InfluxDBMiddleware': 990,
        }
    }

    def extract_item_urls(self, response):
        try:
            data = json.loads(response.body)
            item_urls = [item["DetailPage"] for item in data["SearchResult"]["Products"]]
            mth = re.search(r"SearchParameter=(.+?)%26%40Page%3D(\d+)", response.url)
            page_count = int(data["SearchResult"]["PageCount"])
            current_page = int(mth.group(2))
            if page_count == current_page:
                response.meta["sp"] = None
            else:
                response.meta["sp"] = unquote(mth.group(1)) + "&@Page=" + str(current_page + 1)
        except Exception:
            item_urls = [response.urljoin(x) for x in
                         set(response.xpath("|".join(self.item_xpath)).extract())]
            have_next = "".join(set(response.xpath("//li/a[@class='next']/@data-queryterm").extract()))
            response.meta["sp"] = have_next + "&@Page=2" if have_next else None
        return item_urls

    def extract_page_url(self, response, effective_urls, item_urls):
        if response.meta["sp"]:
            data = {
                "PageSize": "36",
                "View": "M",
                "SearchParameter": response.meta["sp"]
            }

            response.meta["if_next_page"] = True
            response.meta["callback"] = "parse"
            response.meta["priority"] += 20
            return self.url + "?" + urlencode(data)

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=SwarovskiItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("title", "//h1/text()")
        item_loader.add_value("product_id", response.url, re=r"Web_US/en/(\d+)")
        item_loader.add_xpath("price", [
            '//p[@class="price "]/text()',
            '//div[@class="shopping-box"]//span[@class="new"]/text()'
        ])
        item_loader.add_value("availablity", '')
        item_loader.add_xpath("availablity_reason", [
            '//div[@class="variants"]/h2[@class="lined"]/span/text()',
            '//div[@class="product-not-available"]/p/text()',
        ])
        item_loader.add_xpath("old_price", '//div[@class="shopping-box"]//span[@class="old"]/text()')
        item_loader.add_xpath("size_key", '//select[@id="variation"]/option/@value')
        item_loader.add_xpath("size_value", '//select[@id="variation"]/option/text()')
        item_loader.add_value("size", "")
        item_loader.add_xpath("features", '//ul[@class="desc-features"]/li/text()')
        item_loader.add_xpath("description", '//span[@itemprop="description"]/p/text()')
        item_loader.add_xpath("image_urls", '//li/a/img/@data-elevatezoomlargeimg')
