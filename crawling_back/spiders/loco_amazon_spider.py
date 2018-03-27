# -*- coding:utf-8 -*-
from scrapy.http import Request

from . import JaySpider
from ..items.amazon_item import AmazonUpdateItem
from .utils import enrich_wrapper, CustomLoader
from .exception_process import parse_method_wrapper

class LocoAmazonSpider(JaySpider):

    name = "loco_amazon"
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
    # 商品下一页的xpath表达式
    page_xpath = (
        '//div[@id="pagn"]//span[@class="pagnRA"]/a/@href',
        '//a[@id="pagnNextLink"]/@href',
    )

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
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
        #'crawling.downloadermiddlewares.CustomCookiesMiddleware': 585,
        "crawling.downloadermiddlewares.CustomProxyMiddleware": 588,
        'crawling.downloadermiddlewares.AmazonCurlCaptchaRedisCachedMiddleware': 589,
        'crawling.downloadermiddlewares.CustomRedirectMiddleware': 600,
        }
    }

    @parse_method_wrapper
    def parse(self, response):
        self.logger.debug("Start response in parse. ")
        item_urls = [response.urljoin(x) for x in set(response.xpath("|".join(self.item_xpath)).extract())]
        if "if_next_page" in response.meta:
            del response.meta["if_next_page"]
        else:
            response.meta["seed"] = response.url
        response.meta["callback"] = "parse_item"
        response.meta["priority"] -= 20
        for item_url in item_urls:
            response.meta["url"] = item_url
            self.crawler.stats.inc_total_pages(response.meta['crawlid'])
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          errback=self.errback)
        next_page_urls = [response.urljoin(x) for x in
                          set(response.xpath("|".join(self.page_xpath)).extract())]
        # 防止代理继承  add at 16.10.26
        response.meta.pop("proxy", None)
        response.meta["callback"] = "parse"
        response.meta["priority"] += 20
        total_pages = self.redis_conn.hget("crawlid:%s" % response.meta["crawlid"], "total_pages")
        if int(total_pages) >= 300:
            next_page_urls = []
        for next_page_url in next_page_urls:
            response.meta["url"] = next_page_url
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=AmazonUpdateItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        item_loader.add_xpath("parent_asin", '//input[@id="ASIN"]/@value')
        item_loader.add_re("parent_asin", r'"parent_asin":"(.*?)"')
        item_loader.add_value("product_id", "")

        item_loader.add_xpath("title", '//span[@id="productTitle"]/text()')
        item_loader.add_xpath("product_specifications", [
            '//div[@id="technicalSpecifications_feature_div"]//table',
            '//div[@id="prodDetails"]//div[@class="column col1 "]//table',
        ])
        item_loader.add_xpath("product_description", '//div[@id="productDescription"]//p/text()')
        item_loader.add_xpath("feature", '//div[@id="feature-bullets"]/ul|//div[@id="feature-bullets"]/div/ul')
        item_loader.add_re("color_images", [
            r'data\["colorImages"\]\s=\s(.*);',
            r"\'colorImages\'\:\s(\{.*\}),"
        ])
        item_loader.add_value("image_urls", "")
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
                                        '//span[@id="priceblock_ourprice"]/text()'])