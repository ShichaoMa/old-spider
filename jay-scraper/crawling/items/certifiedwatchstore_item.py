# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, duplicate, re_search

from . import BaseItem


def availability_processor(values, loader_context):
    return not bool(loader_context["item"]["availability_reason"].count("OUT OF"))


def stock_processor(values, loader_context):
    return int(re_search(r"(\d+)", loader_context["item"]["availability_reason"], default=0))


class CertifiedwatchstoreItem(BaseItem):
    title = Field()
    product_id = Field()
    special_price = Field(default="$0")
    msr_price = Field(default="$0")
    availability_reason = Field()
    availability = Field(output_processor=availability_processor, order=1)
    stock = Field(output_processor=stock_processor, order=1, default=0)
    description = Field(input_processor=MapCompose(format_html_string))
    upc = Field()
    image_urls = Field(output_processor=duplicate, default=list())
