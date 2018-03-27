# -*- coding:utf-8 -*-
import re
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import TakeAll, format_html_string, safely_json_loads


class JoesnewbalanceoutletiItem(BaseItem):
    product_id = Field()
    title = Field()
    price = Field(input_processor=MapCompose(lambda price: "$%s"%price))
    color = Field()
    skus = Field(input_processor=MapCompose(safely_json_loads))
    children = Field(input_processor=MapCompose(safely_json_loads))
    detail = Field(input_processor=MapCompose(format_html_string))
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=TakeAll())
