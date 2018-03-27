# -*- coding:utf-8 -*-
import re
import os
import socket

from functools import partial
from scrapy.loader.processors import MapCompose, Join
from toolkit import re_search, safely_json_loads, rid, strip
from . import JaySpider
from ..items.amazon_item import AmazonBaseItem, AmazonSkuItem, \
    AmazonUpdateItem, shipping_cost_processor
from ..utils import enrich_wrapper, CustomLoader, xpath_exchange, ItemCollectorPath, extract_specs


class AmazonSpider(JaySpider):

    name = "amazon"
    # 商品详情页链接的xpath表达式或re表达式
    item_xpath = (
        # 从商品标题获取商品详情页url
        '//div[@id="resultsCol"]//div[@class="a-row a-spacing-micro"]/a/@href',
        # 从商品价格获取商品详情页url， 对于sell from others 有可能直接获取到了other sellers的页面。
        # '//div[@id="resultsCol"]//div[@class="a-row a-spacing-none"]/a/@href',
        '//h2/../@href',
        '//div[@id="mainResults"]/ul/li//a[@class="a-link-normal s-access-detail-page  a-text-normal"]/@href',
        '//div[@id="resultsCol"]//div[@class="a-row a-spacing-top-mini"]/a[@class="a-link-normal '
        's-access-detail-page  a-text-normal"]/@href',
    )
    # 商品下一页的表达式
    page_xpath = (r'(.*?)(page=1)(\d+)(.*)',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },

        "DOWNLOADER_MIDDLEWARES": {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
        'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
        'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
        'crawling.downloadermiddlewares.CustomUserAgentMiddleware': 400,
        # Handle timeout retries with the redis scheduler and logger
        'crawling.downloadermiddlewares.NewFixedRetryMiddleware': 510,
        # custom cookies to not persist across crawl requests
        # cookie中间件需要放在验证码中间件后面，验证码中间件需要放到代理中间件后面
        # 'crawling.downloadermiddlewares.CustomCookiesMiddleware': 585,
        "crawling.downloadermiddlewares.CustomProxyMiddleware": 588,
        'crawling.downloadermiddlewares.AmazonCurlCaptchaRedisCachedMiddleware': 589,
        'crawling.downloadermiddlewares.CustomRedirectMiddleware': 600,
        },
    }

    @staticmethod
    def get_base_loader(response):
        if response.meta.get("extend", True):
            return CustomLoader(item=AmazonBaseItem())
        else:
            return CustomLoader(item=AmazonUpdateItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_re("parent_asin", r'"parent_asin":"(.*?)"')
        item_loader.add_value("parent_asin", re_search(r'dp/(\w*)/', response.url))
        item_loader.add_re("product_id", r'"parent_asin":"(.*?)"')
        item_loader.add_value("product_id", re_search(r'dp/(\w*)/', response.url))
        item_loader.add_value("product_id", re_search(r'product/(\w*)/', response.url))
        if response.meta["tags"].get("type") == "ENRICH":
            return
        item_loader.add_xpath("node_ids", '//div[@id="wayfinding-breadcrumbs_feature_div"]//a/@href', re=r'node=(\w+)')
        similar_node_ids = [[re_search(r'node=(\w+)', link) for link in p.xpath('a/@href').extract()]
                            for p in response.xpath('//div[@id="browse_feature_div"]/div/p')]
        item_loader.add_value("similar_node_ids", similar_node_ids)
        item_loader.add_xpath("brand", '//a[@id="bylineInfo"]/text()', MapCompose(partial(rid, old="+", new=" ")))
        item_loader.add_xpath("brand", '//a[@id="brand"]/text()', MapCompose(strip))
        item_loader.add_xpath("brand", '//a[@id="brand"]/@href', re=r'^/(.*)/b/')
        item_loader.add_re("gender", r"p%5Fn%5Ftarget%5Faudience%5Fbrowse-bin%3A(\d+)")
        item_loader.add_re("dimensions_display", r'"dimensionsDisplay"\s?:\s?(.*?]),')
        item_loader.add_re("variations_data", r'"dimensionValuesDisplayData"\s?:\s?({.*?}),')
        item_loader.add_re("color_images", [
            r'data\["colorImages"\]\s=\s(.*);',
            r"\'colorImages\'\:\s(\{.*\}),"
        ])
        item_loader.add_value("image_urls", "")
        if response.meta.get("extend", True):

            skus = safely_json_loads(
                re_search(r'"dimensionValuesDisplayData"\s?:\s?({.*?}),', response.body)).keys() or\
                   [re_search([r'product/(\w*)/', r'dp/(\w*)/'], response.url)]
            for sku in skus:
                response.meta["item_collector"].add_item_loader(ItemCollectorPath(os.path.join(
                           str(response.meta["path"]), "skus#%s"%sku)),
                    CustomLoader(item=AmazonSkuItem()))
            return [{"url": response.urljoin("/gp/product/%s/ref=twister_dp_update?ie=UTF8&psc=1"%sku),
                       "meta": {"path": ItemCollectorPath(os.path.join(
                           str(response.meta["path"]), "skus#%s"%sku))}} for sku in skus]
        else:
            return self.enrich_skus(item_loader, response)

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        item_loader.add_xpath("title", '//span[@id="productTitle"]/text()')
        item_loader.add_value("url", response.url)
        item_loader.add_xpath("part_number", ['//th[contains(text(), "Part")]/following-sibling::td/text()',
                                              '//th[contains(text(), "Artikelnummer")]/following-sibling::td/text()',
                                              '//th[contains(text(), "型番")]/following-sibling::td/text()'])
        item_loader.add_xpath("model_number", ['//th[contains(text(), "Model number")]/following-sibling::td/text()',
                                               '//th[contains(text(), "Modell")]/following-sibling::td/text()',
                                               '//th[contains(text(), "型番")]/following-sibling::td/text()'])
        item_loader.add_xpath("mpn", ['//th[contains(text(), "Part")]/following-sibling::td/text()',
                                      '//th[contains(text(), "Artikelnummer")]/following-sibling::td/text()',
                                      '//th[contains(text(), "型番")]/following-sibling::td/text()'])
        specs = extract_specs(response.selector, '//div[@id="technicalSpecifications_feature_div"]//table//tr')
        item_loader.add_value("product_specifications", specs)
        item_loader.add_xpath("product_description", '//div[@id="productDescription"]//p/text()')
        item_loader.add_xpath("feature", '//div[@id="feature-bullets"]/ul|//div[@id="feature-bullets"]/div/ul')
        item_loader.add_value("asin", re_search(r'product/(\w*)/', response.url))
        item_loader.add_xpath("merchantID", '//input[@id="merchantID"]/@value')
        item_loader.add_xpath(
            "from_price", '//div[@id="mbc"]/div[@class="a-box"]/div/span/span[@class="a-color-price"]/text()')
        item_loader.add_value("stock", "")
        if response.url.count(".com"):
            item_loader.add_value("currency", "USD")
        elif response.url.count(".de"):
            item_loader.add_value("currency", "EUR")
        else:
            item_loader.add_value("currency", "JPY")
        item_loader.add_xpath("availability_reason", [
            '//div[@id="availability"]/span/text()',
            '//span[@id="availability"]/text()',
            '//span[@class="availRed"]/text()',
            '//span[@class="availGreen"]/text()',
            '//div[@id="merchant-info"]/text()',
            '//span[@id="pa_avaliability_message"]/div//text()',
        ], MapCompose(strip), Join(" "))
        item_loader.add_value("availability", "")
        item_loader.add_xpath("list_price", [
            "//div[@id='price']//span[@class='a-text-strike']/text()",
            '//div[@id="price"]//tr[1]/td[2]/text()',
            '//span[@id="listPriceValue"]/text()',
        ])
        item_loader.add_xpath("shipping_cost", [
            '//*[@id="ourprice_shippingmessage"]/span/b/text()',
            '//*[@id="ourprice_shippingmessage"]/span/text()',
            '//*[@id="saleprice_shippingmessage"]/span/b/text()',
            '//*[@id="saleprice_shippingmessage"]/span/text()',
        ])
        item_loader.add_xpath("price", ['//*[@id="unqualifiedBuyBox"]//span[@class="a-color-price"]/text()',
                                        '//span[@id="actualPriceValue"]/b/text()',
                                        '//span[@id="priceblock_dealprice"]/text()',
                                        '//span[@id="priceblock_saleprice"]/text()',
                                        '//span[@id="priceblock_ourprice"]/text()',
                                        '//span[@class="a-declarative"]//span[@class="a-size-medium a-color-price"]/text()'], MapCompose(strip))
        #next_url = response.xpath('//span[@class="a-size-small"]/a/@href|//*[@id="availability"]//a/@href')
        if response.url.count("co.jp"):
            return
        # 不全抓取 第三方
        next_url = response.xpath('//*[@id="availability"]//a/@href')

        if next_url:
            next_url = response.urljoin(xpath_exchange(next_url))
            offer = response.xpath('//span[@class="a-size-small"]/a/@href')
            if not next_url.count("redirect") or next_url.count("redirect") and offer:
                next_url = response.urljoin(xpath_exchange(offer)) if next_url.count("redirect") else next_url
                try:
                    item_loader.add_value("other", self.offer_request(next_url))
                except Exception as e:
                    self.logger.error("Error in offer listing request: %s" % e)
                    response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
                        str(response.meta["path"]), "other"))] = item_loader
                    return [{"url": response.urljoin(next_url),
                             "meta": {"path": ItemCollectorPath(os.path.join(
                                 str(response.meta["path"]), "other"))}}]
            else:
                # 可能是其它网站的， 不抓取
                self.logger.info("Other site: %s"%next_url)
                # other = get_from_other_site(next_url, "http://%s:%s/"%(
                #         self.settings.get("SP_HOST"), self.settings.get("SP_PORT", 8888)), "zappos")
                # if "error" in other:
                #     self.logger.error("Error in enrich other: %s"%other)
                # item_loader.add_value("other", other)

    def offer_request(self, next_url):
        client = socket.socket()
        try:
            client.connect((self.settings.get("DRIVER_HOST"), self.settings.getint("DRIVER_PORT")))
            client.send(next_url.encode("utf-8"))
            other = client.recv(10240)
            client.close()
            if other != b"error":
                other = [{"price": line[0].strip(), "shipping_cost": shipping_cost_processor(line[1]),
                          "merchant": line[2].strip()}
                         for line in safely_json_loads(other.decode("utf-8"))]
                self.logger.debug("Got offer listing data: %s" % str(other))
                return other
            else:
                raise Exception("503 error. ")
        finally:
            client.close()

    @enrich_wrapper
    def enrich_other(self, item_loader, response):
        self.logger.info("Start to enrich other. ")
        other_sel = response.xpath('//div[@class="a-section a-padding-small"]/div')
        other = [seller for seller in [{"price": xpath_exchange(
            line.xpath("div[1]/span[1]/text()")), "shipping_cost": shipping_cost_processor(
            xpath_exchange(line.xpath("div[1]/p/span").xpath("string(.)"))),
            "item_info": re.sub(r"<.*?>", " ", xpath_exchange(line.xpath("div[3]/ul"))).replace("\n", ""),
            "merchant": xpath_exchange(line.xpath("div[4]/h3/span/a/text()"))}
            for line in other_sel.xpath('div[@class="a-row a-spacing-mini olpOffer"]')] if
            seller["price"].strip()]
        item_loader.add_value("other", other)
        # 可以抓取所有第三个方，支持翻页。
        # next_url = response.xpath('//li[@class="a-last"]/a/@href')
        # if next_url:
        #     response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
        #         str(response.meta["path"]), "other"))] = item_loader
        #     return [{"url": response.urljoin(xpath_exchange(next_url)),
        #              "meta": {"path": ItemCollectorPath(os.path.join(
        #                  str(response.meta["path"]), "other"))}}]

    def need_duplicate(self, url):
        return url