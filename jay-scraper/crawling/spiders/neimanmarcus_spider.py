# -*- coding:utf-8 -*-
import os
import time
import json
import base64

from scrapy import Selector

from toolkit import re_search, safely_json_loads

from . import JaySpider
from ..items.neimanmarcus_item import NeimanmarcusItem
from ..utils import enrich_wrapper, CustomLoader, ItemCollectorPath


class NeimanmarcusSpider(JaySpider):
    name = "neimanmarcus"
    # 商品详情页链接的xpath表达式或re表达式
    item_xpath = (
        '//a[@id="productTemplateId"]/@href',
    )
    custom_settings = {
        "ITEM_PIPELINES": {
            'crawling.pipelines.%s_pipeline.%sKafkaPipeline' % (name, name.capitalize()): None if JaySpider.debug else 100,
            'crawling.pipelines.%s_pipeline.%sFilePipeline' % (name, name.capitalize()): 100 if JaySpider.debug else None,
        },
    }

    def extract_page_url(self, response, effective_urls, item_urls):
        uri = response.meta['url'].split("#")[-1]
        try:
            d = dict([(k, v) for k, v in map(lambda x: x.split("="), uri.split("&"))])
        except Exception:
            d = {}
        refinements = d.get("refinements", "")
        response.meta["category_id"] = response.meta.setdefault(
            "category_id", ''.join(response.xpath('//div[@id="endecaContent"]/@categoryid').extract()))
        response.meta.setdefault("page_offset", 0)
        if "static_errorpage" not in response.url and (response.meta.get("page_offset") == 0 or len(item_urls)):
            response.meta["seed"] = response.meta["seed"] or response.url
            data = {
                "GenericSearchReq": {
                    "pageOffset": response.meta.get("page_offset"),
                    "pageSize": "30",
                    "refinements": refinements,
                    "selectedRecentSize": "",
                    "activeFavoriteSizesCount": "0",
                    "activeInteraction": "true",
                    "mobile": False,
                    "sort": "PCS_SORT",
                    "definitionPath": "/nm/commerce/pagedef_rwd/template/EndecaDrivenHome",
                    "userConstrainedResults": "true",
                    "rwd": "true",
                    "advancedFilterReqItems": {
                        "StoreLocationFilterReq":
                            [{
                                "allStoresInput": "false",
                                "onlineOnly": "",
                                'locationInput': '',
                                'radiusInput': '100'
                            }]
                    },
                    "categoryId": "%s" % response.meta["category_id"],
                    "sortByFavorites": False,
                    "isFeaturedSort": False,
                    'updateFilter': 'false',
                    "prevSort": ""
                }
            }
            form_data = {
                "data": '$b64$' + base64.b64encode(json.dumps(data).encode()).replace(b'=', b'$').decode(),
                "service": "getCategoryGrid",
                "bid": "GenericSearchReq",
                "sid": "getCategoryGrid",
                "timestamp": '%s' % int(time.time()*1000)
            }
            response.meta["if_next_page"] = True
            response.meta["callback"] = "parse"
            response.meta["priority"] += 20
            return ['https://www.neimanmarcus.com/en-hk/category.service?instart_disable_injection=true',
                     self.parse, "POST", {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                     "&".join("%s=%s" % (k, v) for k, v in form_data.items())]

    def extract_item_urls(self, response):
        try:
            context = json.loads(response.body)
            sel = Selector(text=context["GenericSearchResp"]["productResults"])
            response.meta["page_offset"] = context["GenericSearchResp"]["pageNumber"]
            response.meta["refinements"] = context["GenericSearchResp"]["refinements"]
            return [response.urljoin(x) for x in set(sel.xpath("|".join(self.item_xpath)).extract())]
        except Exception:
            return []

    @staticmethod
    def get_base_loader(response):
        return CustomLoader(item=NeimanmarcusItem())

    @enrich_wrapper
    def enrich_data(self, item_loader, response):
        self.logger.debug("Start to enrich data. ")
        product_id = re_search(r'"product_id":\["(.*?)"\]', response.body)
        item_loader.add_value("product_id", product_id)
        item_loader.add_re("price", r'"product_price":\s*?\["(.*?)"\]')
        item_loader.add_xpath("features", '//div[@itemprop="description"]/div/ul/li/text()')
        data = {"ProductSizeAndColor": {"productIds": product_id}}
        color_names = response.css("li.color-picker").xpath("@data-color-name").extract()
        color_keys = response.css("li.color-picker").xpath("@data-color-key").extract()

        if not color_names:
            item_loader.add_xpath('image_urls', '//img[@itemprop="image"]/@data-zoom-url')
        else:
            item_loader.add_value("colors", dict(zip(color_names, color_keys)))
            sub_loader = item_loader.nested_css("li.color-picker")
            sub_loader.add_xpath("color_images", "@data-sku-img")
        form_data = {
            "data": '$b64$' + base64.b64encode(json.dumps(data).encode()).replace(b'=', b'$').decode(),
            "bid": "ProductSizeAndColor",
            "sid": "getSizeAndColorData",
            "timestamp": '%s' % int(time.time() * 1000)
        }
        response.meta["item_collector"].item_loaders[ItemCollectorPath(os.path.join(
            str(response.meta["path"]), "skus"))] = item_loader
        return [{"url": "https://www.neimanmarcus.com/en-cn/product.service", "method": "POST",
                 "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                 "body": "&".join("%s=%s" % (k, v) for k, v in form_data.items()),
                 "meta": {"path": ItemCollectorPath(os.path.join(str(response.meta["path"]), "skus"))}}]

    @enrich_wrapper
    def enrich_skus(self, item_loader, response):
        self.logger.debug("Start to enrich skus. ")
        data = safely_json_loads(safely_json_loads(response.body)["ProductSizeAndColor"]["productSizeAndColorJSON"])[0]
        item_loader.add_value("title", data["productName"])
        item_loader.add_value("skus", data["skus"])
