# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose, Join
from toolkit import format_html_string

from . import BaseItem
from ..utils import TakeAll


class MichaelkorsItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field(output_processor=Join())
    feature = Field(output_processor=TakeAll())
    specification = Field(input_processor=MapCompose(format_html_string))
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=TakeAll())
