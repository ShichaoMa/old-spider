# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import  format_html_string, TakeAll


def image_urls_processor(value):
    return value + "?req=tile&rect=0,0,3000,3000&fmt=jpg"


class WatchstationItem(BaseItem):
    product_id = Field()
    title = Field()
    old_price = Field()
    price = Field()
    feature = Field(input_processor=MapCompose(format_html_string))
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(input_processor=MapCompose(image_urls_processor), output_processor=TakeAll(),
                       default=list())
