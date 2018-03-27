# -*- coding:utf-8 -*-
import re
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import TakeAll, format_html_string


def image_urls_processor(values):
    return ["https:%s"%value for value in values]


class GucciItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field()
    color = Field()
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor)
