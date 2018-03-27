# -*- coding:utf-8 -*-
import re
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values):
    return [re.sub(r"(_)(13)(_)", "\g<1>16\g<3>", value) for value in values]


class ArmaniItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field()
    color = Field(output_processor=TakeAll())
    size = Field(output_processor=TakeAll())
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor)
