# -*- coding: utf-8 -*-
from functools import reduce, partial

from scrapy import Field
from scrapy.loader.processors import MapCompose, Compose, Join

from . import BaseItem
from ..utils import chain_all, format_html_string, safely_json_loads, strip


def product_id_processor(value, loader_context):
    return loader_context["item"]['utag_data']['product_id'][0]


def product_assetId_processor(value, loader_context):
    return str(loader_context["item"]['utag_data']['product_assetId'][0])


def skus_processor(value, loader_context):
    item = loader_context["item"]
    return reduce(lambda a, b: a if a.get('itemNbr') == item['product_id'] else b, item['all_skus'])


def color_images_processor(body, loader_context):
    item = loader_context["item"]
    return item["product_images"][item["product_assetId"]]


def image_urls_processor(value, loader_context):
    item = loader_context["item"]
    return list(set("https://dm.victoriassecret.com/%s/760x1013/%s.jpg"%(
            'p' if z['image'].count('tif/') else 'product', z['image'])
                                           for z in chain_all(item['color_images'].values())))


class VictoriassecretItem(BaseItem):
    product_id = Field(output_processor=product_id_processor, order=1)
    title = Field(output_processor=Compose(MapCompose(strip), Join()))
    description = Field(input_processor=MapCompose(format_html_string))
    utag_data = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    product_assetId = Field(output_processor=product_assetId_processor, order=1)
    all_skus = Field(input_processor=MapCompose(partial(safely_json_loads, defaulttype=list)),
                     output_processor=lambda values: values, default=list(), skip=True)
    skus = Field(output_processor=skus_processor, order=1)
    selectors = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    atpdata = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    product_images = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    item_number = Field()
    color_images = Field(output_processor=color_images_processor, default=dict(), order=2)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=3)

