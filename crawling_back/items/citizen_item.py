# -*- coding:utf-8 -*-
from functools import partial

from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, duplicate


class CitizenItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field()
    description = Field()
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=partial(duplicate, key=lambda x: "http://citizen.jp%s"%x))
