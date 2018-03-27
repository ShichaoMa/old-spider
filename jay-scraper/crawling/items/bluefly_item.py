# -*- coding: utf-8 -*-
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose
from toolkit import chain_all

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values, loader_context):

    color_meta = loader_context["item"]["colors"]
    color_images = dict()
    for color in color_meta:
        color_images[color["color_id"]] = color["image_urls"]
    return color_images


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


class BlueflyItem(BaseItem):
    product_id = Field()
    colors = Field(output_processor=TakeAll())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=1)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=2)


class BlueflyColorItem(Item):
    color_id = Field()
    title = Field()
    features = Field(output_processor=TakeAll())
    skus = Field(output_processor=TakeAll())
    color = Field()
    sizes = Field(default=dict())
    image_urls = Field(input_processor=MapCompose(lambda value: "http:%s" % value.strip()),
                       output_processor=TakeAll(), default=list())

