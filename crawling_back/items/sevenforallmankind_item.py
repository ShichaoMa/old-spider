# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import safely_json_loads, TakeAll


def product_id_processor(values, loader_context):
    return loader_context["item"]["pagedata"]["product"]


def title_processor(values, loader_context):
    return loader_context["item"]["pagedata"]["title"]


def sku_processor(values, loader_context):
    item = loader_context["item"]
    return item["pagedata"]["product%s"%item["product_id"]]["SkuPrices"]


def colors_processor(values, loader_context):
    item = loader_context["item"]
    return item["pagedata"]["product%s" % item["product_id"]]["ProductColors"]


def size_processor(values, loader_context):
    item = loader_context["item"]
    return item["pagedata"]["product%s" % item["product_id"]]["ProductSizes"]


def image_urls_processor(values):
    return [y for y in set("http://%s"%i for i in values) if not y.count("thumb") and not y.count("regular")]


def description_processor(values, loader_context):
    item = loader_context["item"]
    return "\n".join(
            [item["pagedata"]["product%s"%item["product_id"]].get(key) for key in filter(
                lambda key: key.startswith("Description"), item["pagedata"]["product%s"%item["product_id"]].keys())])


class SevenforallmankindItem(BaseItem):
    pagedata = Field(input_processor=MapCompose(safely_json_loads), skip=True)
    product_id = Field(output_processor=product_id_processor, order=1)
    title = Field(output_processor=title_processor, order=1)
    sku = Field(output_processor=sku_processor, order=2, default=list())
    colors = Field(output_processor=colors_processor, order=2, default=list())
    size = Field(output_processor=size_processor, order=2, default=list())
    description = Field(output_processor=description_processor, order=2)
    image_urls = Field(input_processor=image_urls_processor, output_processor=TakeAll(), default=list())
