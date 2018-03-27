# -*- coding:utf-8 -*-
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, chain_all

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values, loader_context):
    return chain_all(color["image_urls"] for color in loader_context["item"]["colors"])


def color_images_processor(values, loader_context):
    return dict((color["color"], color["image_urls"]) for color in loader_context["item"]["colors"])


class KenzoItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    colors = Field(output_processor=TakeAll())
    description = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    color_images = Field(output_processor=color_images_processor, order=1, default=dict())


class KenzoColorItem(Item):
    url = Field()
    price = Field()
    color = Field()
    color_id = Field()
    timestamp = Field()
    status_code = Field()
    sizes = Field(output_processor=TakeAll())
    image_urls = Field(output_processor=TakeAll(), default=list())
    availabilities = Field(output_processor=TakeAll())