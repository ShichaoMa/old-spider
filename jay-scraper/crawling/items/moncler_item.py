# -*- coding:utf-8 -*-
import re
from scrapy import Field
from scrapy.loader.processors import MapCompose, Compose
from toolkit import format_html_string, safely_json_loads, chain_all

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(value):
    color_images = dict()
    for color_id, images in value.items():
        for image in images:
            color_images.setdefault(color_id, []).append(re.sub(r"(?<=_)(\d+)(?=_)", "14", image))
    return color_images


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


class MonclerItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    description = Field(input_processor=MapCompose(format_html_string))
    feature = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    color_images = Field(output_processor=Compose(MapCompose(color_images_processor), chain_all), default=dict())
    skus = Field(output_processor=TakeAll(), default=list())
    sizes = Field(input_processor=MapCompose(safely_json_loads), output_processor=TakeAll())
    prices = Field(output_processor=chain_all)
