# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import TakeAll, chain_all, format_html_string, safely_json_loads


def product_id_processor(values, loader_context):
    return loader_context["item"]["prodID"]


def product_images_processor(values):
    return list(set(values))


def image_urls_processor(response_urls, loader_context):
    item = loader_context["item"]
    return [urljoin(response_urls[0], i) for i in item["product_images"]]


class AshfordItem(BaseItem):
    prodID = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    Retail = Field()
    ashford_price = Field(default="$0")
    sale_price = Field(default="$0")
    Save = Field()
    Weekly_Sale = Field()
    Your_price = Field(default="$0")
    prodName = Field()
    prod_desc = Field()
    detail = Field(input_processor=MapCompose(format_html_string))
    Brand = Field()
    product_images = Field(input_processor=product_images_processor,
                           output_processor=TakeAll(), default=list())
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=1)
    chinese_detail = Field(input_processor=MapCompose(format_html_string))

