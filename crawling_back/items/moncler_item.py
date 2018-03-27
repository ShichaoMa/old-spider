# -*- coding:utf-8 -*-
import re
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import TakeAll, format_html_string, duplicate, safely_json_loads, re_search, chain_all


def product_images_processor(values):
    return duplicate(re.sub(r"(?<=_)(\d+)(?=_)", "14", value) for value in values)


def color_images_processor(values, loader_context):
    color_ids = loader_context["item"]["color_ids"]
    product_images = loader_context["item"]["product_images"]
    return dict((color_id, [re.sub(
        r"(?<=(?:\d/))(\w+?)(?=_)", color_id, image) for image in product_images]) for color_id in color_ids)


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


def color_ids_processor(values, loader_context):
    return [re_search(r"/\d+/(\w+?)_", color["Image"]) for color in loader_context["item"]["colors"]]


class MonclerItem(BaseItem):
    product_id = Field()
    colors = Field(input_processor=MapCompose(safely_json_loads), output_processor=TakeAll())
    part_number = Field()
    title = Field()
    description = Field(input_processor=MapCompose(format_html_string))
    feature = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor, order=3, default=list())
    product_images = Field(output_processor=product_images_processor, default=list())
    color_images = Field(output_processor=color_images_processor, order=2, default=dict())
    color_ids = Field(output_processor=color_ids_processor, order=1)
    skus = Field(output_processor=TakeAll(), default=list())
    sizes = Field(input_processor=MapCompose(safely_json_loads), output_processor=TakeAll())