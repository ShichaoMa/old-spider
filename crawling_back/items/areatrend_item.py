# -*- coding:utf-8 -*-
import re

from functools import partial
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import safely_json_loads, format_html_string, re_search


def color_images_processor(value, loader_context):
    item = loader_context["item"]
    return dict((k, [re_search(r"/([^/]*?)\.jpg", v["value"])])
                for k, v in item["color_size"].get("131", {}).items()) or \
           {"": [item["product_id"]]}


def image_urls_processor(values, loader_context):
    item = loader_context["item"]
    new_color_images = dict()
    image_urls = list()
    for value in values:
        for k, v in item["color_images"].items():
            url = re.sub(r"(upload/)([\d\-]+)(.*?jpg)", "\g<1>%s\g<3>" % v[0], value.get("full"))
            image_urls.append(url)
            new_color_images.setdefault(v[0], []).append(url)
    item["color_images"] = new_color_images
    return image_urls


class AreatrendItem(BaseItem):
    product_id = Field()
    title = Field()
    skus = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    old_price = Field(default="$0")
    special_price = Field(default="$0")
    color_size = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    feature = Field(input_processor=MapCompose(format_html_string))
    color_images = Field(output_processor=color_images_processor, order=1, default=dict())
    description = Field(input_processor=MapCompose(format_html_string))
    detail = Field(input_processor=MapCompose(format_html_string))
    image_urls = Field(input_processor=MapCompose(partial(safely_json_loads, defaulttype=list)),
                       output_processor=image_urls_processor, order=2, default=list())
    spec = Field(input_processor=MapCompose(format_html_string))
    availability = Field()
    ware = Field()
