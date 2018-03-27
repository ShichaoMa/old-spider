# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import safely_json_loads

from . import BaseItem
from ..utils import TakeAll


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
    return ["http://%s"%i for i in values]


def description_processor(values, loader_context):
    item = loader_context["item"]
    return item["pagedata"]["product%s"%item["product_id"]]["Description1"]
    # return "\n".join(
    #         [item["pagedata"]["product%s"%item["product_id"]].get(key) for key in filter(
    #             lambda key: key.startswith("Description"), item["pagedata"]["product%s"%item["product_id"]].keys())])


def features_processor(values, loader_context):
    item = loader_context["item"]
    features = list()
    for key in filter(lambda key: key.startswith("Description"), item["pagedata"]["product%s"%item["product_id"]].keys()):
        if key == "Description1":
            continue
        features.extend(item["pagedata"]["product%s" % item["product_id"]].get(key).split("<br/>\r\n"))
    return features


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    colors = item["colors"]
    return {colors[0]["Id"]: item["image_urls"]}


class SevenforallmankindItem(BaseItem):
    pagedata = Field(input_processor=MapCompose(safely_json_loads), skip=True)
    product_id = Field(output_processor=product_id_processor, order=1)
    title = Field(output_processor=title_processor, order=1)
    sku = Field(output_processor=sku_processor, order=2, default=list())
    colors = Field(output_processor=colors_processor, order=2, default=list())
    size = Field(output_processor=size_processor, order=2, default=list())
    description = Field(output_processor=description_processor, order=2)
    features = Field(output_processor=TakeAll())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=3)
    image_urls = Field(input_processor=image_urls_processor, output_processor=TakeAll(), default=list())
