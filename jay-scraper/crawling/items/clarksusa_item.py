# -*- coding:utf-8 -*-
from scrapy import Field, Item
from scrapy.loader.processors import MapCompose
from toolkit import safely_json_loads, chain_all

from . import BaseItem
from ..utils import TakeAll


def product_id_processor(value):
    return value.replace(" ", "_")


def image_urls_processor(value):
    return ["http://clarks.scene7.com/is/image/%s?scl=1&rect=0,0,%s,%s&fmt=jpg" % (
        item["i"]["n"], item["dx"], item["dy"]) for item in (
        value["set"]["item"] if isinstance(value["set"]["item"], list) else [value["set"]["item"]])]


def sizes_widths_processor(values):
    return dict(zip(values[:len(values)//2], values[len(values)//2:]))


def color_images_processor(values, loader_context):
    color_images = dict()
    for color in loader_context["item"]["colors"]:
        color_images[color["color_id"]] = color["image_urls"]
    return color_images


def _image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


class ClarksusaItem(BaseItem):
    product_id = Field(input_processor=MapCompose(product_id_processor))
    title = Field()
    specs = Field(output_processor=TakeAll())
    description = Field()
    colors = Field(output_processor=TakeAll())
    color_images = Field(output_processor=color_images_processor, order=1, default=dict())
    image_urls = Field(output_processor=_image_urls_processor, order=2, default=list())


class ClarksusaColorItem(Item):
    color_id = Field()
    color = Field()
    price = Field()
    availabilities = Field(input_processor=MapCompose(safely_json_loads))
    sizes = Field(input_processor=sizes_widths_processor)
    widths = Field(input_processor=sizes_widths_processor)
    image_urls = Field(input_processor=MapCompose(safely_json_loads, image_urls_processor),
                       output_processor=TakeAll(), default=list())
