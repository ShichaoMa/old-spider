# -*- coding:utf-8 -*-
from . import JaySpider
from ..items.jomashop_item import JomashopItem
from ..utils import CustomLoader, enrich_wrapper, xpath_exchange


class JomashopSpider(JaySpider):
    name = "jomashop"
    item_xpath = ('//ul[@class="products-grid"]/li/div/a[@class="product-image"]/@href',)
    page_xpath = (r'(.*?)(p=1)(\d+)(.*)',)

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
        #'crawling.downloadermiddlewares.CustomCookiesMiddleware': 585,
        'crawling.downloadermiddlewares.JomashopCpatchaMiddleware':586,
        "crawling.downloadermiddlewares.CustomProxyMiddleware": 588,
        'crawling.downloadermiddlewares.CustomRedirectMiddleware': 600,
        },
        #"COOKIES": """__ibxl=1;_uetsid=_uetddbb32df;bounceClientVisit355v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgO6kB0AVgPYC2AhinFRGQMa1EgA0IATjCFLFKtBkxbsaIAL5A;2c.cId=5a97a27360b24c16fe29239f;_vuid=2e34fae8-f68f-4aba-bbac-db3c01d75333;STSID874673=cd684969-0639-49ae-ab7e-c2d029e9a8c9;GSIDgn7uqQ6V9PiU=c6ebe199-3431-484d-aef6-314da04c4209;_gat_t3=1;_gat=1;_gid=GA1.2.201856261.1519886953;_ga=GA1.2.219460631.1519886953;__roit=0;ftr_dtnx_1d=1519886953751;ftr_blst_1h=1519886953747;__wid=783037716;ftr_ncd=6;D_HID=99664E09-0DD5-3FB8-BA04-C89878D790EE;D_ZUID=235E6A34-602F-339B-A7AE-6D6B49607BAE;D_ZID=AE67374A-3DD6-3242-9E35-F4D956BBD96D;D_UID=D8B673C2-9C34-333A-B25C-93CF76EA7416;D_IID=E9192341-CED7-36A9-AFEC-9CE03E3709BC;forterToken=d457631b2c3c4280ba563a0b09fbbee5_1519886951555__UDF4_6;_gat_JomashopAnalyticsSanityCheck=1;_vwo_uuid_v2=D288FB1BC97E40CFD124B10C928FC043A|bf0cace2284022eea1320be3c85b096e;frontend=4e32a49b24894489807660d20322c057;D_SID=23.83.247.116:ttkfFqjekoBSB3zoyWbVErPi6wivc+B47JibUzfsDq0;__cfduid=d771cd0edcb21d7a7941f06c917cc479a1519886924;"""
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=JomashopItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("brand_name", '//form[@id="product_addtocart_form"]//span[@class="brand-name"]/text()')
        item_loader.add_xpath("product_name", '//form[@id="product_addtocart_form"]//span[@class="product-name"]/text()')
        item_loader.add_re("product_ids", r'"sku": "(.+?)"')
        item_loader.add_xpath("model_number", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_xpath("mpn", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_xpath("part_number", '//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()', re=r"Item No. (\S+)")
        item_loader.add_value("product_id", "")
        item_loader.add_xpath("final_price",
                              '//*[@id="product_addtocart_form"]//p[@class="final-price"]'
                              '/meta[@itemprop="price"]/@content')
        item_loader.add_xpath("retail_price",
                              '//*[@id="product_addtocart_form"]//li[@class="pdp-retail-price"]/span/text()')
        item_loader.add_xpath("savings", '//*[@id="product_addtocart_form"]//li[@class="pdp-savings"]/span/text()')
        item_loader.add_xpath("availability_reason", ['//span[@class="large-availability"]/text()',
                                                      '//span[@class="instock"]/text()'])
        image_value = xpath_exchange(response.xpath('//input[@name="product"]/@value'))
        item_loader.add_xpath("image_urls", [
            '//div[@id="MagicToolboxSelectors%s"]/a/@href' % image_value,
            '//a[@id="MagicZoomPlusImage%s"]/@href' % image_value
        ])
        item_loader.add_xpath("details", '//dd[@id="tab-container-details"]')
        item_loader.add_xpath("description", '//div[@class="product-description"]/div/text()')
        specs = [[xpath_exchange(li.xpath("label//text()")), xpath_exchange(li.xpath("div//text()"))]
                 for li in response.xpath('//div[@class="product-attributes"]//ul/li')]
        item_loader.add_value("specs", specs)
        item_loader.add_xpath("Color", [
            '//span[@id="Dial Color"]/text()',
            '//span[@id="Color"]/text()',
        ])
        item_loader.add_xpath("upc", '//span[@id="UPC Code"]/text()')
