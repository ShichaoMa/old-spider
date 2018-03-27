# -*- coding:utf-8 -*-
from scrapy import Field

from . import BaseItem
from ..utils import TakeAll


class DieselItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field()
    color = Field(output_processor=TakeAll())
    image_urls = Field(output_processor=TakeAll())
