# -*- coding:utf-8 -*-
import re

from scrapy import Field, Item

from toolkit import chain_all

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values, loader_context):
    color_images = dict()
    regex = re.compile(r"(?<=sw\=)(\d+)(?=\&sh\=)(&sh=)(\d+)")
    for color_id, color in loader_context["item"]["colors"].items():
        if not color["image_urls"]:
            color_images.setdefault(color["color_id"], []).append(
                "https://us.shop.ecco.com/dw/image/v2/AAJX_PRD/on/demandware.static/-/Sites-ecco/default/"
                "dw60759de6/images/hi-res/%s/%s/01_%s_%s.jpg?sw=1024&sh=1024&sm=fit" % (
                loader_context["item"]["product_id"], color_id, loader_context["item"]["product_id"], color_id))
        for image_url in color["image_urls"]:
            color_images.setdefault(color["color_id"], []).append(regex.sub("1024\g<2>1024", image_url))
    return color_images


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


def colors_processor(values):
    return dict((value["color_id"], value) for value in values)


class EccoItem(BaseItem):
    product_id = Field()
    title = Field()
    size = Field(output_processor=TakeAll())
    description = Field()
    features = Field(output_processor=TakeAll())
    color_images = Field(output_processor=color_images_processor, order=1, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=2)
    colors = Field(output_processor=colors_processor, default=dict())


class EccoColorItem(Item):
    sizes = Field(output_processor=TakeAll())
    color = Field()
    color_id = Field()
    standard_price = Field()
    sales_price = Field()
    image_urls = Field(output_processor=TakeAll())
