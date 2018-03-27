# -*- coding: utf-8 -*-
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, safely_json_loads, groupby, re_search

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    return groupby(item["image_urls"], key=lambda x: re_search(r"s7-(\d+)", x))


def image_urls_processor(value):
    items = value["set"]["item"]
    if isinstance(items, dict):
        items = [items]
    image_urls = list()
    for item in items:
        if "dx" in item:
            image_urls.append(
                "https://s7.ralphlauren.com/is/image/%s?wid=%s&hei=%s" % (item["i"]["n"], item["dx"], item["dy"]))
    return image_urls


class RalphlaurenItem(BaseItem):
    product_id = Field()
    product_name = Field()
    skus = Field(output_processor=TakeAll(), default=list())
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(input_processor=MapCompose(safely_json_loads, image_urls_processor),
                       output_processor=TakeAll(), default=list())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=1)


class RalphlaurenSkuItem(Item):
    id = Field()
    price = Field(default="$0")
    standard_price = Field(default="$0")
    color = Field()
    color_id = Field()
    size = Field()
    status = Field()
    width = Field()
