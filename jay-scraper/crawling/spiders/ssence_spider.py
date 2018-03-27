# -*- coding:utf-8 -*-

from . import JaySpider
from ..utils import CustomLoader, enrich_wrapper
from ..items.ssence_item import SsenceItem


class SsenceSpider(JaySpider):
    name = "ssence"
    # 分类抓取的时候使用这两个属性
    item_xpath = ('//div[@class="browsing-product-list"]//a/@href',)
    page_xpath = ('//li[@class="last-page"]/following-sibling::li/a/@href',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
        "COOKIES": "visid_incap_1637567=31aX7d2GSi6FK0hB7BU75F7gqVoAAAAAQUIPAAAAAAC63Fyzw3Ocw974JbCmJe/z; incap_ses_982_1637567=kwC+DtjjyD0a26mj+sOgDV7gqVoAAAAAzrr1rJLyVQUK2W5CZPsoIw==; visitorId=4b00006039f8258a5f504187f955a2b3539fe6de96af2764394c714d33be5016; forcedCountry=ca; nlbi_1637567=61K5fcIGsTgM9x2AjefZEAAAAAB2kt3duNa25ASthbqYAgYV; lang=en_CA; shopping_bag=8BB9EC2FC2A74F449B16A23100715E12; NavigationSessions:token=21f310f69f931da49b3d745dbc9cbf37; country=ca; _ga=GA1.2.1279904075.1521082468; _gid=GA1.2.1370170999.1521082468; __zlcmid=lRhBwxaTYiQAHT; _uetsid=_uet330e40d1"
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=SsenceItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("title", '//h2/text()')
        item_loader.add_xpath("description", '//p[@class="vspace1 product-descr'
                                             'iption-text"]/span/text()')
        item_loader.add_xpath("price", '//h3/span/text()')
        item_loader.add_xpath(
            "sizes", '//select[@id="size"]/option[not(@disabled)]/@value')
        item_loader.add_xpath("product_id", '//span[@itemprop="sku"]/text()')

        item_loader.add_xpath("image_urls", '//div[@class="image-wrapper"]/'
                                            'div/picture/img/@data-srcset')
