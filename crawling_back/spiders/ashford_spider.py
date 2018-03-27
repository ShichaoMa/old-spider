# -*- coding:utf-8 -*-
import os
import time
from . import JaySpider
from ..items.ashford_item import AshfordItem
from .utils import CustomLoader, enrich_wrapper, ItemCollectorPath


class AshfordSpider(JaySpider):
    name = "ashford"
    item_xpath = ('//div[@id="grid-4-col"]/div/div[2]/div/div/div/a[1]/@href',)
    page_xpath = ('//*[@id="bottomPager"]/li[@class="nextLink"]/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=AshfordItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_re("prodID", r'"sku_code":"(.*?)"')
        item_loader.add_xpath("model_number", '//*[@id="prodID"]/text()')
        item_loader.add_xpath("part_number", '//*[@id="prodID"]/text()')
        item_loader.add_xpath("mpn", '//*[@id="prodID"]/text()')
        if not response.xpath('//*[@id="prodID"]/text()'):
            path = ItemCollectorPath(os.path.join(str(response.meta["path"]), "data"))
            response.meta["item_collector"].add_item_loader(path, item_loader)
            return [{"url": response.url, "meta": {"path": path}}]
        item_loader.add_value("product_id", '')
        item_loader.add_xpath("Retail", '//*[@id="pricing"]/tbody/tr[contains(th,"Retail")]/td/text()')
        item_loader.add_xpath("ashford_price", [
            '//*[@id="pricing"]/tbody/tr[contains(th,"Ashford")]/td/text()',
            '//table[@id="pricing"]/tbody/tr[@class="ashford_price"]/td/text()',
        ])
        item_loader.add_xpath("sale_price", '//table[@id="pricing"]/tbody/tr[1]/td/text()')
        item_loader.add_xpath("Save", '//*[@id="pricing"]/tbody/tr[contains(th,"Save")]/td/text()')
        item_loader.add_xpath("Weekly_Sale", '//*[@id="pricing"]/tbody/tr[contains(th,"Weekly")]/td/text()')
        item_loader.add_xpath("Your_price", [
            '//*[@id="pricing"]/tbody/tr[contains(th,"Your")]/td/text()',
            '//td[@class="highlight"]/text()',
        ])
        item_loader.add_xpath("prodName", '//*[@id="prodName"]/a/text()')
        item_loader.add_xpath("prod_desc", '//*[@id="fstCont"]/h3/text()')
        item_loader.add_xpath("detail", '//div[@id="tab1_info"]')
        item_loader.add_xpath("Brand", '//h1[@id="prodName"]/a[@id="sameBrandProduct"]/text()[1]')
        item_loader.add_xpath("product_images", '//a[contains(@href,"/images/catalog/") and contains(@href,"XA.jpg")]/@href')
        item_loader.add_value("image_urls", response.url)
        chinese_detail_url = response.url.replace('www.', 'zh.')
        path = ItemCollectorPath(os.path.join(str(response.meta["path"]), "chinese_detail"))
        response.meta["item_collector"].add_item_loader(path, item_loader)

        return [{"url": chinese_detail_url,
                 "meta": {"dont_update_cookies": True, "cookie": "userPrefLanguage=zh_CN", "path": path}}]

    @enrich_wrapper
    def enrich_chinese_detail(self, item_loader, response):
        self.logger.debug("Start to enrich chinese_detail. ")
        item_loader.add_xpath("chinese_detail", '//div[@id="tab1_info"]')