# -*- coding: utf-8 -*-
from functools import partial
from base64 import decodebytes

from scrapy import Field
from scrapy.loader.processors import MapCompose, Join
from toolkit import encode, chain_all, format_html_string, safely_json_loads, rid

from . import BaseItem


def product_processor(values, loader_context):
    return loader_context["item"]["product_info"].get("product")


def color_images_processor(values, loader_context):
    return dict((color["colorId"], color["images"]) for
                color in loader_context["item"]["product"].get("detail", {}).get("styles", []))


def image_urls_processor(values, loader_context):
    return ["https://m.media-amazon.com/images/I/%s.jpg" % image["imageId"]
             for image in chain_all(loader_context["item"]["color_images"].values())]


class SixpmItem(BaseItem):
    product_id = Field()
    title = Field(output_processor=Join())
    productDescription = Field(input_processor=MapCompose(
        format_html_string, partial(rid, old="View Zappos.com Glossary of Terms", new="")))
    product_info = Field(input_processor=MapCompose(safely_json_loads), skip=True, default=dict())
    product = Field(output_processor=product_processor, default=dict(), order=1)
    color_images = Field(output_processor=color_images_processor, default=dict(), order=2)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=3)
