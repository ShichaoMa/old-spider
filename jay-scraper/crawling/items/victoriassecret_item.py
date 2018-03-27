# -*- coding: utf-8 -*-
from functools import partial

from scrapy import Field
from scrapy.loader.processors import MapCompose, Compose, Join
from toolkit import chain_all, format_html_string, safely_json_loads, strip, duplicate

from ..utils import TakeFirst

from . import BaseItem


def product_id_processor(values, loader_context):
    if 'product_assetId' in loader_context["item"]['utag_data']:
        return loader_context["item"]['utag_data']['product_assetId'][0]


def price_info_processor(values, loader_context):
    return [i for i in values if i["assetId"] == loader_context["item"]['product_id']]


def stock_info_processor(values, loader_context):
    item = loader_context["item"]
    if item["atpdata"]:
        return item["atpdata"]['atpData'][str(item["product_id"])]


def color_images_processor(values, loader_context):
    item = loader_context["item"]
    if item["product_images"]:
        return item["product_images"][str(item["product_id"])]


def selector_processor(value, loader_context):
    return dict(duplicate(value[str(loader_context["item"]["product_id"])]["color"]["options"],
                          keep=lambda x: (x["value"], x["label"])))


def image_urls_processor(values, loader_context):
    item = loader_context["item"]
    return list(set("https://dm.victoriassecret.com/%s/760x1013/%s.jpg" % (
            'p' if z['image'].count('tif/') else 'product', z['image'])
                                           for z in chain_all(item['color_images'].values())))


class VictoriassecretItem(BaseItem):
    product_id = Field(output_processor=product_id_processor, order=1)
    title = Field(output_processor=Compose(MapCompose(strip), Join()))
    description = Field(input_processor=MapCompose(format_html_string))
    utag_data = Field(input_processor=MapCompose(safely_json_loads), default=dict(), skip=True)
    stock_info = Field(output_processor=stock_info_processor, order=2)
    price_info = Field(input_processor=MapCompose(partial(safely_json_loads, defaulttype=list)),
                       output_processor=price_info_processor, order=2, default=list())
    atpdata = Field(input_processor=MapCompose(safely_json_loads), default=dict(), skip=True)
    selector = Field(output_processor=Compose(MapCompose(safely_json_loads, selector_processor), TakeFirst()), order=2)
    features = Field(output_processor=Compose(partial(map, strip), partial(filter, None), list))
    product_images = Field(input_processor=MapCompose(safely_json_loads), default=dict(), skip=True)
    color_images = Field(output_processor=color_images_processor, default=dict(), order=2)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=3)

