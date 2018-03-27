# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose, Join

from . import BaseItem
from ..utils import format_html_string, TakeAll


class InvictawatchItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field(output_processor=Join(" "))
    price = Field()
    description = Field(input_processor=MapCompose(format_html_string))
    detail = Field(input_processor=MapCompose(format_html_string),
                   output_processor=Join("\n"))
    image_urls = Field(output_processor=TakeAll())
