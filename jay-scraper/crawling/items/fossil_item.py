# -*- coding:utf-8 -*-
import re
from functools import partial
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, duplicate, safely_json_loads

from . import BaseItem


class FossilItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    sku_collection = Field(input_processor=MapCompose(safely_json_loads))
    description = Field(input_processor=MapCompose(format_html_string))
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=partial(
        duplicate, key=lambda x: re.sub(r"(?<=\?)(.*)", "$aemResponsive_pdpzoom$", x)))
