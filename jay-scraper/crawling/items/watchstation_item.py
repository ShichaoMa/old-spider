# -*- coding: utf-8 -*-
from urllib.parse import urlparse, urlunparse

from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, safely_json_loads

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(value):
    return ["http://fossil.scene7.com/is/image/%s?scl=2&req=tile&rect=0,0,2000,2000&fmt=jpg"%item["i"]["n"]
            for item in value["set"]["item"]]


class WatchstationItem(BaseItem):
    product_id = Field()
    title = Field()
    old_price = Field()
    price = Field()
    specs = Field(output_processor=TakeAll())
    feature = Field(input_processor=MapCompose(format_html_string))
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(input_processor=MapCompose(safely_json_loads, image_urls_processor), output_processor=TakeAll(),
                       default=list())
