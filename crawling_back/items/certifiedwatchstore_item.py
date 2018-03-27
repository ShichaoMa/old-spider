# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import Compose, format_html_string, duplicate


class CertifiedwatchstoreItem(BaseItem):
    title = Field()
    product_id = Field()
    special_price = Field(default="$0")
    msr_price = Field(default="$0")
    availability_reason = Field()
    description = Field(input_processor=MapCompose(format_html_string))
    upc = Field()
    image_urls = Field(output_processor=duplicate, default=list())
