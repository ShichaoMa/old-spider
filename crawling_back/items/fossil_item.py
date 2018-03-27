# -*- coding:utf-8 -*-
import re
from functools import partial
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, safely_json_loads, duplicate


class FossilItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    sku_collection = Field(input_processor=MapCompose(safely_json_loads))
    description = Field(input_processor=MapCompose(format_html_string))
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=partial(
        duplicate, key=lambda x: re.sub(r"(?<=\?)(.*)", "$aemResponsive_pdpzoom$", x)))
