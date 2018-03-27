# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, replace_dot, wrap_key, chain_all, groupby, re_search, safely_json_loads

from . import BaseItem
from ..utils import TakeAll


def product_id_processor(values, loader_context):
    return loader_context["item"]["sku"]


def sku_processor(values, loader_context):
    products = loader_context["item"]["products"]
    return products.get("sku") or products.get("id") or "".join(values)


def skus_collection_processor(values, loader_context):
    return loader_context["item"]["products"].get("skusCollection")


def color_images_processor(values, loader_context):
    return groupby(loader_context["item"]['image_urls'], lambda y: re_search(r"/([^/_]+)[^/]*?\.jpg", y))


def image_urls_processor(value):
    return "http:%s" % value.strip()


class BackcountryItem(BaseItem):
    products = Field(input_processor=MapCompose(wrap_key, safely_json_loads, replace_dot),
                     output_processor=chain_all, default=dict(), skip=True)
    product_id = Field(output_processor=product_id_processor, order=2)
    title = Field()
    description = Field()
    features = Field(output_processor=TakeAll())
    specs = Field(output_processor=TakeAll())
    sku = Field(output_processor=sku_processor, order=1)
    skus_collection = Field(output_processor=skus_collection_processor, order=1, default=dict())
    details = Field(input_processor=MapCompose(format_html_string))
    color_images = Field(output_processor=color_images_processor, default=dict(), order=1)
    image_urls = Field(input_processor=MapCompose(image_urls_processor),
                       output_processor=TakeAll(), default=list())

