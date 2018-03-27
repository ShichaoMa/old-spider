# -*- coding:utf-8 -*-
import os
import hashlib

from toolkit import re_search
from . import JaySpider
from ..items.clarksusa_item import ClarksusaItem, ClarksusaColorItem
from ..utils import CustomLoader, enrich_wrapper, extract_specs, ItemCollectorPath


class ClarksusaSpider(JaySpider):
    name = "clarksusa"
    item_xpath = ('//div[contains(@class, "productGridItem")]/a/@href',)
    page_xpath = (r'(.*?)(page=0)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=ClarksusaItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_xpath("title", '//h1/text()')
        item_loader.add_xpath("product_id", '//h1/text()')
        specs = extract_specs(response.selector, '//table[@class="featureTable"]//tr')
        item_loader.add_value("specs", [[spec[0].strip(), spec[1].strip().replace("<br>", "")]for spec in specs])
        item_loader.add_xpath("description", '//span[@id="Description"]/text()')
        color_urls = response.xpath('//ul[@class="colorlist"]/li/a/@href').extract()
        for color_url in color_urls:
            response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                str(response.meta["path"]), "colors#%s" % hashlib.sha1(
                    color_url.encode("utf-8")).hexdigest()))] = CustomLoader(item=ClarksusaColorItem())
        return [{"url": response.urljoin(color_url), "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "colors#%s" % hashlib.sha1(color_url.encode("utf-8")).hexdigest()))}}
                for color_url in color_urls]

    @enrich_wrapper
    def enrich_colors(self, item_loader, response):
        item_loader.add_xpath("color_id", '//span[@class="sku"]/text()')
        item_loader.add_xpath("price", '//span[@id="currentPrice"]/text()')
        item_loader.add_xpath("color", '//span[@class="code"]/text()')
        item_loader.add_xpath("availabilities", '//select[@id="Size"]/@data-matrix')
        item_loader.add_xpath("sizes", ['//select[@id="Size"]/option[@data-prompt-value]/@value',
                                        '//select[@id="Size"]/option/@data-prompt-value'])
        item_loader.add_xpath("widths", ['//select[@id="Fit"]/option[@data-prompt-value]/@value',
                                         '//select[@id="Fit"]/option[@data-prompt-value]/text()'])
        image_set_url = re_search(r"url: '(.*?)'", response.body)
        response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
            str(response.meta["path"]), "image_urls#%s" % hashlib.sha1(
                image_set_url.encode("utf-8")).hexdigest()))] = item_loader
        return [{"url": image_set_url, "meta": {"path": ItemCollectorPath(os.path.join(
                     str(response.meta["path"]), "image_urls#%s" % hashlib.sha1(
                image_set_url.encode("utf-8")).hexdigest()))}}]

    @enrich_wrapper
    def enrich_image_urls(self, item_loader, response):
        item_loader.add_re("image_urls", r's7jsonResponse\((.*?),""\);')

    def need_duplicate(self, url):
        return re_search(r"/(\w+-\w*)-[^/]+?/p", url)
