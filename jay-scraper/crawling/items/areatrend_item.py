# -*- coding:utf-8 -*-
from functools import partial
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import safely_json_loads, format_html_string, re_search, chain_all, duplicate

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values, loader_context):
    if loader_context["item"]["skus"].get("attributes"):
        color_images = dict()
        images = loader_context["item"]["skus"]["images"]
        indices = loader_context["item"]["skus"]["index"]
        for key, image in images.items():
            color_images.setdefault(indices[key]["131"], set()).update(duplicate(image, keep=lambda x: x["full"]))
        return color_images
    else:
        return {"init": duplicate(values, keep=lambda x: x["full"])}


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


class AreatrendItem(BaseItem):
    product_id = Field()
    title = Field()
    skus = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    old_price = Field()
    special_price = Field()
    color_size = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    features = Field(output_processor=TakeAll())
    color_images = Field(input_processor=MapCompose(partial(safely_json_loads, defaulttype=list)),
                         output_processor=color_images_processor, order=1, default=dict())
    description = Field()
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(output_processor=image_urls_processor, order=2, default=list())
    specs = Field(output_processor=TakeAll())
    availability = Field()
    ware = Field()
