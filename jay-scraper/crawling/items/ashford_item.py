# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose, Join, Compose
from toolkit import format_html_string, strip

from . import BaseItem
from ..utils import TakeAll


def product_id_processor(values, loader_context):
    return loader_context["item"]["prodID"]


def product_images_processor(values):
    return list(set(values))


def image_urls_processor(value):
    return "https://www.ashford.com" + value


def availability_processor(values, loader_context):
    return "Out Of Stock" not in loader_context["item"]["availability_reason"]


class AshfordItem(BaseItem):
    prodID = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    Retail = Field()
    ashford_price = Field(default="$0")
    sale_price = Field(default="$0")
    Save = Field()
    Weekly_Sale = Field()
    Your_price = Field(default="$0")
    prodName = Field(input_processor=Join())
    prod_desc = Field()
    detail = Field(input_processor=MapCompose(format_html_string))
    Brand = Field()
    image_urls = Field(input_processor=MapCompose(image_urls_processor), output_processor=TakeAll(), default=list())
    chinese_detail = Field(input_processor=MapCompose(format_html_string))
    specs = Field(output_processor=TakeAll())
    condition = Field(output_processor=Compose(Join(), strip))
    availability = Field(output_processor=availability_processor, order=1, default=False)
    availability_reason = Field()
