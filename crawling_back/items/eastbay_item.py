# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import format_html_string, TakeAll, re_search, safely_json_loads, re_size


def nbr_processor(values, loader_context):
    if values:
        return values[0]
    else:
        re_search(r"model:(\d+)/", loader_context["item"]["url"])


def product_id_processor(values, loader_context):
    return loader_context["item"]["NBR"]


def inet_copy_processor(values, loader_context):
    return loader_context["item"]["model"].get('INET_COPY')


def image_urls_processor(value):
    try:
        data = value["set"]["item"]
        if isinstance(data, dict):
            data = [data]
    except KeyError:
        data = []
    return ["http://images.footlocker.com/is/image/%s?wid=%s&hei=%s&fmt=jpg"%(
            (i["i"]["n"], ) + re_size(i["dx"], i["dy"])) for i in data]


def color_images_processor(values):
    return [tuple(values)]


class EastbayItem(BaseItem):
    product_id = Field(output_processor=product_id_processor, order=2)
    title = Field()
    NBR = Field(output_processor=nbr_processor, order=1)
    description = Field(input_processor=MapCompose(format_html_string))
    INET_COPY = Field(output_processor=inet_copy_processor, order=1)
    model = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    styles = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    color_images = Field(output_processor=dict, default=dict())
    image_urls = Field(input_processor=MapCompose(safely_json_loads, image_urls_processor),
                       output_processor=TakeAll(), default=list())
