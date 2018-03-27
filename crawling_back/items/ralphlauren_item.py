# -*- coding: utf-8 -*-
from functools import partial

from scrapy import Field, Item
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, TakeAll, chain_all, safely_json_loads, groupby, re_search


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    return groupby(item["image_urls"], key=lambda x: re_search(r"s7-(\d+)", x))


def image_urls_processor(value):
    items = value["set"]["item"]
    if isinstance(items, dict):
        items = [items]
    return ["https://s7.ralphlauren.com/is/image/%s?wid=%s&hei=%s" % (item["i"]["n"], item["dx"], item["dy"]) for item in items]


def is_available_processor(values, loader_context):
    reason = loader_context["item"]["status"].lower()
    have = ['in stock']
    if not reason or [x for x in have if reason.startswith(x.lower())]:
        return "true"
    else:
        return "false"


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
    is_available = Field(output_processor=is_available_processor, order=1)
    status = Field()
