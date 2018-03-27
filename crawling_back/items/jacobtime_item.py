# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string


def product_id_processor(values, loader_context):
    return loader_context["item"]["products_id"]


def image_urls_processor(value, loader_context):
    return urljoin(loader_context["item"]["response_url"], value)


class JacobtimeItem(BaseItem):
    brand = Field()
    descript_title = Field()
    products_id = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    retail = Field()
    your_price = Field(default="$0")
    details = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=MapCompose(image_urls_processor),
                       default=list(), order=1)
    upc_or_ean = Field()
