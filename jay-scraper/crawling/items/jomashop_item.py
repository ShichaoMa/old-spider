# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, duplicate

from ..utils import TakeAll
from . import BaseItem


def product_id_processor(values, loader_context):
    return loader_context["item"]["product_ids"]


def availability_processor(values, loader_context):
    return not bool(loader_context["item"]["availability_reason"].count("Out of"))


class JomashopItem(BaseItem):
    brand_name = Field()
    product_name = Field()
    product_ids = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    final_price = Field(default="$0")
    retail_price = Field(default="$0")
    savings = Field()
    # shipping = Field()
    # shipping_availability = Field()
    availability_reason = Field()
    availability = Field(output_processor=availability_processor, order=1, default=False)
    image_urls = Field(output_processor=duplicate, default=list(), order=1)
    details = Field(input_processor=MapCompose(format_html_string))
    specs = Field(output_processor=TakeAll())
    description = Field()
    Color = Field()
    upc = Field()

