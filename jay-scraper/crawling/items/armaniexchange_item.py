# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import Join, MapCompose
from toolkit import format_html_string

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values, loader_context):
    return [value.split(",")[0].split(" ")[0] for value in values]


class ArmaniexchangeiItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field(output_processor=Join())
    color = Field(output_processor=TakeAll())
    size = Field(output_processor=TakeAll())
    description = Field(input_processor=MapCompose(format_html_string))
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor)
