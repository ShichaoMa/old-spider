# -*- coding: utf-8 -*-
import re
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, TakeAll, chain_all, re_search


def image_urls_processor(values, loader_context):
    colors = loader_context["item"]["colors"]
    color_ids = [color_id.replace("-", "_") for color_id in colors.keys()]
    return chain_all([re.sub(r"(?<=/)(\w+)(?=_)", color_id, "https:%s"%value.replace("\r\n", "")) for value in values] for color_id in color_ids)


def color_images_processor(values, loader_context):
    color_images = dict()
    image_urls = loader_context["item"]["image_urls"]
    regex = re.compile(r"(?<=/)(\w+)(?=_)")
    for image_url in image_urls:
        color_images.setdefault(re_search(regex, image_url), []).append(image_url)
    return color_images


class FinishlineItem(BaseItem):
    product_id = Field()
    title = Field()
    productDescription = Field(input_processor=MapCompose(format_html_string))
    color_images = Field(output_processor=color_images_processor, order=2, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    prices = Field(output_processor=TakeAll())
    colors = Field(default=dict())
    sizes = Field(default=dict())
