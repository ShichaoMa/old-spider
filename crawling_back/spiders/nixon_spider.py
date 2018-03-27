# -*- coding:utf-8 -*-
"""
spider编写规则
1 spider必须继承自StructureSpider
2 若执行分类抓取则需要配置item_pattern = (), page_pattern = ()，其中：
    1）item_pattern元组中的元素为分类页中每个item链接所对应的xpath表达式
    2）page_pattern元组中的元素可以是下一页链接所所对应的正则表达式，或者其它规则，详见https://github.com/ShichaoMa/webWalker/wiki/%E9%80%9A%E7%94%A8%E6%8A%93%E5%8F%96%E9%85%8D%E7%BD%AE%E6%96%B9%E6%B3%95
3 提供get_base_loader静态方法，传入response，返回CustomLoader对应一个Item
4 提供enrich_data方法，必须被enrich_wrapper装饰，其中：
    1）传入item_loader, response，使用item_loader的方法(add_value, add_xpath, add_re)添加要抓取的属性名及其对应表达式或值。
    2）如该次渲染需要产生新的请求，则通过response.meta["item_collector"]提供的(add, extend)方法，
       则将(prop, item_loader, request_meta)添加到item_collector中。其中：
        prop: 指下次请求获取的全部字段如果做为一个子item返回时，子item在其父item中对应的字段名称。
        item_loader: 用来抽取下次请求中字段的item_loader，如果下次请求返回子item，则此item_loader与父级item_loader不同
        request_meta: 组建request所需要的kwargs type: dict
4 下次请求所回调的enrich函数名称为 enrich_`prop`
"""
from . import JaySpider
from .utils import CustomLoader, enrich_wrapper
from ..items.nixon_item import NixonItem


class NixonSpider(JaySpider):
    name = "nixon"
    # 分类抓取的时候使用这两个属性
    item_xpath = ('//ul/li/div/div/a/@href',)
    page_xpath = ('start=0',)

    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.KafkaPipeline': None if JaySpider.debug else 100,
        },
    }

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=NixonItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        item_loader.add_xpath("product_id", '//span[@itemprop="productID"]/text()')
        item_loader.add_xpath("part_number", '//span[@itemprop="productID"]/text()')
        item_loader.add_xpath("price", '//span[@id="price-sales"]/text()')
        item_loader.add_xpath("colors", '//ul/li/a/@data-lgimg')
        item_loader.add_xpath("feature", '//dl[@class="pdp-features_list"]')
        item_loader.add_xpath("spec", '//ul[@class="product-attributes-group_list"]')
        item_loader.add_xpath("image_urls", '//img[@class="productthumbnail"]/@data-lgimg')

    def need_duplicate(self, url):
        return url