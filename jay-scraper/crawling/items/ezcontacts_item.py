# -*- coding:utf-8 -*-
import re

from scrapy import Field
from scrapy.loader.processors import MapCompose

from toolkit import safely_json_loads, duplicate, re_search, chain_all, groupby

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


def color_images_processor(values, loader_context):
    return dict(
        (color["id"], [color["zoom_src"]]) for c, color in loader_context["item"]["product"]["colorOptions"].items())


def product_id_processor(values, loader_context):
    return loader_context["item"]["product"]["groupProductId"]


class EzcontactsItem(BaseItem):
    product_id = Field(output_processor=product_id_processor, order=1)
    product = Field(input_processor=MapCompose(safely_json_loads))
    title = Field()
    price = Field()
    list_price = Field()
    image_urls = Field(output_processor=image_urls_processor, order=2)
    color_images = Field(output_processor=color_images_processor, order=1)
