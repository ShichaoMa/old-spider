# -*- coding:utf-8 -*-
import re
from urllib.parse import urlparse, urlunparse

from scrapy import Item, Field
from scrapy.loader.processors import MapCompose, Compose

from . import BaseItem
from ..utils import format_html_string, chain_all, re_search, TakeAll, groupby, duplicate


def image_urls_processor(values, loader_context):
    values = [urlunparse(urlparse(value)._replace(query="")) for value in values]
    views = groupby(values, lambda value: re_search(r"((?:(?!_)\w)+)$", value))
    colors = loader_context["item"]["colors"].keys()
    for view, images in views.items():
        if len(images) > 1:
            continue
        else:
            for image in images[:]:
                if image.count("_") >= 2:
                    for color in colors:
                        images.append(re.sub(r"(_)(\w*?)(_\w+)", "\g<1>%s\g<3>"%color, image))

    return chain_all(views.values())


def current_color_processor(value):
    return re_search([r'dwvar_color=(\w+)'], value).lower()


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    return groupby(item["image_urls"], lambda value: re_search(r"_(.*?)_\w+", value) or item["current_color"])


class CoachBaseItem(BaseItem):
    product_id = Field()
    title = Field()
    current_color = Field(input_processor=MapCompose(current_color_processor), skip=True)
    description = Field(input_processor=MapCompose(format_html_string))
    details = Field(input_processor=MapCompose(format_html_string))
    colors = Field(output_processor=lambda values: dict(
        (value.get("color").get("id").lower(), dict(value)) for value in values), default=dict())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=2)
    image_urls = Field(output_processor=Compose(image_urls_processor, duplicate),
                       default=list(), order=1)


class CoachColorItem(Item):
    sales_price = Field(default="$0")
    color = Field()
    size = Field(output_processor=TakeAll())
