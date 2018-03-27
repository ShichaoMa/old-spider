# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import safely_json_loads, chain_all, duplicate

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    if item["skus"]:
        return dict((sku["color"] or "init", sku["image_urls"]) for sku in item["skus"])
    else:
        return {item["color"]: item["image_urls"]}


def image_urls_processor(values, loader_context):
    if values:
        return ["http://images10.newegg.com/productimage/" + i for i in values[0].split(",")]
    return duplicate(chain_all(duplicate(loader_context["item"]["skus"], keep=lambda sku: sku["image_urls"])))


class NeweggItem(BaseItem):
    product_id = Field()
    product_info = Field(input_processor=MapCompose(safely_json_loads))
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    color_images = Field(output_processor=color_images_processor, order=2, default=dict())
    skus = Field(output_processor=TakeAll(), default=dict())
    # sku才使用，但对于单商品的页面，也可以使用
    title = Field()
    sku_id = Field()
    size = Field()
    size_id = Field()
    timestamp = Field()
    color = Field()
    color_id = Field()
    stock = Field(input_processor=MapCompose(int), default=0)
    width = Field()
    price = Field()
    list_price = Field()
    description = Field()
    specs = Field(output_processor=TakeAll())


class NeweggSkuItem(NeweggItem):
    image_urls = Field(input_processor=MapCompose(lambda value: ["http://images10.newegg.com/productimage/" + i for i in value.split(",")]),
                       output_processor=TakeAll(), default=list())
