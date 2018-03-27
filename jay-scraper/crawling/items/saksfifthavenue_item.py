# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import Compose
from toolkit import safely_json_loads

from . import BaseItem
from ..utils import TakeAll, TakeFirst


def image_urls_processor(value, loader_context):
    item = loader_context["item"]
    return ["%s%s%s%s%s" % (
            "http:", item['image_server_url'], item['images_path'], y, "?wid=1600&hei=1600&fmt=jpg") for y in value]


class SaksfifthavenueItem(BaseItem):
    product_id = Field()
    title = Field()
    sizes = Field(output_processor=TakeAll())
    features = Field(output_processor=TakeAll())
    color = Field()
    price = Field()
    image_server_url = Field()
    images_path = Field()
    image_urls = Field(
        output_processor=Compose(TakeFirst(), safely_json_loads, image_urls_processor), default=list(), order=1)
