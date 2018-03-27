# -*- coding:utf-8 -*-
from scrapy import Item, Field
from scrapy.loader.processors import MapCompose, Compose
from toolkit import format_html_string, chain_all, re_search, groupby, safely_json_loads

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(value):
    data = safely_json_loads(value.replace("/&quot;", ""))
    items = data["set"]["item"] if isinstance(data["set"]["item"], list) else [data["set"]["item"]]
    return ["http://img1.cohimg.net/is/image/" + item["i"]["n"] for item in items]


def current_color_processor(value):
    return re_search([r'dwvar_color=(\w+)'], value).lower()


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    return groupby(item["image_urls"], lambda value: re_search(r"_(.*?)_\w+", value, default=item["current_color"]))


class CoachBaseItem(BaseItem):
    product_id = Field()
    title = Field()
    current_color = Field(input_processor=MapCompose(current_color_processor), skip=True)
    description = Field(input_processor=MapCompose(format_html_string))
    features = Field(output_processor=TakeAll())
    colors = Field(output_processor=lambda values: dict(
        (value.get("color").get("id").lower(), dict(value)) for value in values), default=dict())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=2)
    image_urls = Field(input_processor=MapCompose(image_urls_processor), output_processor=TakeAll(), default=list())


class CoachColorItem(Item):
    sales_price = Field(default="$0")
    color = Field()
    size = Field(output_processor=TakeAll())
