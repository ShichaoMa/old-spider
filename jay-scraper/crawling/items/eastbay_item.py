# -*- coding:utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, re_search, safely_json_loads, chain_all

from . import BaseItem
from ..utils import TakeAll, re_size


def safe(func):
    def wrapper(value):
        try:
            return func(value)
        except Exception:
            return value
    return wrapper


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
        return ["http://images.footlocker.com/is/image/%s?wid=%s&hei=%s&fmt=jpg" % (
            (i["i"]["n"],) + re_size(i["dx"], i["dy"])) for i in data]
    except KeyError:
        return []
    # except TypeError:
    #     return ["http:" + value] if value else []


def color_images_processor(values, loader_context):
    color_images = dict(values)
    if chain_all(color_images.values()):
        return color_images
    else:
        try:
            return dict(map(lambda x: (x, ["http://images.footlocker.com/pi/%s/zoom/" % x]),
                            loader_context["item"]["model"]["ALLSKUS"]))
        except KeyError:
            pass


class EastbayItem(BaseItem):
    product_id = Field(output_processor=product_id_processor, order=2)
    title = Field()
    NBR = Field(output_processor=nbr_processor, order=1)
    description = Field(input_processor=MapCompose(format_html_string))
    INET_COPY = Field(output_processor=inet_copy_processor, order=1)
    model = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    styles = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=1)
    image_urls = Field(input_processor=MapCompose(safe(safely_json_loads), image_urls_processor),
                       output_processor=TakeAll(), default=list())
