# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import safely_json_loads, groupby, chain_all


def product_name_processor(values, loader_context):
    return loader_context["item"]["initialData"]["Model"]["StyleModel"]["Name"]


def product_id_processor(values, loader_context):
    return loader_context["item"]["initialData"]["Model"]["StyleModel"]["Number"]


def description_processor(values, loader_context):
    return loader_context["item"]["initialData"]["Model"]["StyleModel"]["Description"]


def skus_processor(values, loader_context):
    return loader_context["item"]["initialData"]["Model"]["StyleModel"]["Skus"]


def features_processor(values, loader_context):
    return "<br>".join(loader_context["item"]["initialData"]["Model"]["StyleModel"]["Features"])


def color_images_processor(values, loader_context):
    return groupby(
        loader_context["item"]["initialData"]["Model"]["StyleModel"]["StyleMedia"], lambda x: x.get("ColorId"))


def image_urls_processor(values, loader_context):
    return [i.get("ImageMediaUri", {}).get("Zoom") for i in chain_all(
        loader_context["item"]["color_images"].values())]


class NordstromItem(BaseItem):
    initialData = Field(input_processor=MapCompose(safely_json_loads), skip=True)
    product_name = Field(output_processor=product_name_processor, order=1)
    product_id = Field(output_processor=product_id_processor, order=1)
    description = Field(output_processor=description_processor, order=1)
    features = Field(output_processor=features_processor, order=1)
    skus = Field(output_processor=skus_processor, order=1)
    color_images = Field(output_processor=color_images_processor, order=1, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
