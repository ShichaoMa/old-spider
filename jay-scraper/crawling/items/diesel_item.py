# -*- coding:utf-8 -*-
import re

from scrapy import Field
from scrapy.loader.processors import MapCompose

from toolkit import safely_json_loads, duplicate, re_search, chain_all, groupby

from . import BaseItem
from ..utils import TakeAll


def colors_processor(values):
        return dict(duplicate(
            values, keep=lambda value:
            (re_search(r"([A-Z0-9]+)_[A-Z]\.jpg", value["url"]), value["title"].split(" ")[-1])))


def sizes_processor(values):
    return [re_search(r"_size=(\w+)", value) for value in values]


def image_urls_processor(values, loader_context):
    item = loader_context["item"]
    return chain_all(
        [re.sub(r"[A-Z0-9]+(_[A-Z]\.jpg)", "%s\g<1>" % color_id, value) for color_id in item["colors"]]
        for value in values)


def color_images_processor(values, loader_context):
    return groupby(loader_context["item"]["image_urls"], lambda value: re_search(r"([A-Z0-9]+)_[A-Z]\.jpg", value))


class DieselItem(BaseItem):
    product_id = Field()
    part_number = Field()
    title = Field()
    price = Field()
    colors = Field(input_processor=MapCompose(safely_json_loads), output_processor=colors_processor)
    sizes = Field(output_processor=TakeAll())
    image_urls = Field(output_processor=image_urls_processor, order=1)
    color_images = Field(output_processor=color_images_processor, order=2)
    description = Field()
    features = Field(output_processor=TakeAll())
