# -*- coding:utf-8 -*-
from urllib.parse import urlparse
from toolkit import safely_json_loads

from . import JaySpider
from ..items.michaelkors_item import MichaelkorsItem
from ..utils import CustomLoader, enrich_wrapper


class MichaelkorsSpider(JaySpider):
    name = "michaelkors"
    item_xpath = ('//li[@class="product-brand-container"]/a/@href',)
    page_xpath = ("//a/b/c",)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    def extract_page_url(self, response, effective_urls, item_urls):
        part = urlparse(response.url)
        stateIdentifier = "%s?No=%s&Nrpp=42"%(part.path[part.path.find("_"):], len(item_urls))
        response.meta["if_next_page"] = True
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        return "https://www.michaelkors.com/server/data/guidedSearch?stateIdentifier=" + stateIdentifier

    def extract_item_urls(self, response):
        try:
            return [product["seoURL"] for product in safely_json_loads(response.body)["result"]["productList"]]
        except:
            return [response.urljoin(x) for x in set(response.xpath("|".join(self.item_xpath)).extract())]

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=MichaelkorsItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//div[@class="name"]/h2/text()')
        item_loader.add_xpath("part_number", '//div[@class="name"]/h2/text()')#, '//div[@class="style-number-title"]/span/text()')
        item_loader.add_xpath("price", '//div[@class="price t-size-large"]/span/text()')
        item_loader.add_xpath("feature", '//figure/text()')
        item_loader.add_xpath("title", '//div[@class="name"]/h2/text()')
        item_loader.add_xpath("specification", '//ul[@class="display-list"]')
        item_loader.add_xpath("description", '//div[@class="js-cont-wrap"]/p')
        item_loader.add_xpath("image_urls", '//meta[@property="og:image"]/@content')
