# -*- coding:utf-8 -*
import base64
from toolkit import re_search, debugger

from . import JaySpider
from ..utils import enrich_wrapper, CustomLoader, xpath_exchange
from ..items.finishline_item import FinishlineItem


class FinishlineSpider(JaySpider):
    name = "finishline"
    item_xpath = ('//div[@class="product-card"]/a[@id]/@href',
                  '//div[@class="product-container"]/a[p]/@href',)
    page_xpath = ('No=0',)

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
            'crawling.downloadermiddlewares.LimitedUserAgentMiddleware': 400,
            # Handle timeout retries with the redis scheduler and logger
            'crawling.downloadermiddlewares.NewFixedRetryMiddleware': 510,
            # custom cookies to not persist across crawl requests
            # cookie中间件需要放在验证码中间件后面，验证码中间件需要放到代理中间件后面
            #'crawling.downloadermiddlewares.CustomCookiesMiddleware': 585,
            "crawling.downloadermiddlewares.CustomProxyMiddleware": 588,
            'crawling.downloadermiddlewares.CustomRedirectMiddleware': 600,
        }
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=FinishlineItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        prices = dict((xpath_exchange(price.xpath("@id")),
                       price.xpath("div/span/text()").extract())
                       for price in response.xpath('//div[@class="priceList"]'))
        item_loader.add_value("prices", prices)
        sizes = dict((xpath_exchange(size.xpath("@id")),
                      [{base64.decodebytes(xpath_exchange(option.xpath("@data-sku")).encode()).decode():
                            xpath_exchange(option.xpath("@aria-label"))}
                       for option in size.xpath("ul/li/a|div")]) for size in response.css('div.sizeList'))
        item_loader.add_value("sizes", sizes)
        item_loader.add_value("colors", dict(zip(response.xpath(
            '//div[@id="alternateColors"]//a/@data-productid').extract(), response.xpath(
            '//div[@id="alternateColors"]//a/div/img/@alt').extract())))
        item_loader.add_xpath("image_urls", '//div[@id="mobileImageSlider"]/div/img/@src|//div[@id="alt"]/@data-large')
        item_loader.add_re("product_id", r'productId : "(\w+?)"')
        item_loader.add_xpath("title", '//h1[@id="title"]/text()')
        item_loader.add_xpath("productDescription", [
            '//div[@id="productDescription"]',
            '//h2[@class="ui-product-details__title"]/text()|//div[@class="ui-product-details__description"]/text()',
        ])
        item_loader.add_value("color_images", "")

    def need_duplicate(self, url):
        return re_search(r"(prod\d+)", url)
