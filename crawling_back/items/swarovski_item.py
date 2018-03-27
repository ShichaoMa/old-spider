# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, TakeAll


def size_processor(values, loader_context):
    item = loader_context["item"]
    return dict(zip(item["size_key"][1:], item["size_value"][1:]))


class SwarovskiItem(BaseItem):
    title = Field()
    product_id = Field()
    price = Field(default="$0")
    old_price = Field(default="$0")
    size_key = Field(output_processor=TakeAll(), skip=True)
    size_value = Field(output_processor=TakeAll(), skip=True)
    size = Field(output_processor=size_processor, default=dict(), order=1)
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=TakeAll(), default=list())
