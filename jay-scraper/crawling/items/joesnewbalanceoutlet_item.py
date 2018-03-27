from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, safely_json_loads, wrap_key, chain_all

from . import BaseItem
from ..utils import TakeAll


def color_images_processor(values):
    color_images = dict()
    for value in values:
        for image in safely_json_loads(value):
            color_images.setdefault(image["c"], list()).append(image["f"].replace("\\u0026", "&"))
    return color_images


def image_urls_processor(values, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


def variants_processor(value):
    return [safely_json_loads(value)]


def skus_processor(values, loader_context):
    skus = list()
    for index, variant in enumerate(loader_context["item"]["variants"]):
        for sku in variant:
                sku["price"] = float(loader_context["item"]["prices"][index])
                sku["list_price"] = loader_context["item"]["list_prices"][index]
                sku["stock"] = int(loader_context["item"]["stock"][sku["v"]])
                skus.append(sku)
    return skus


class JoesnewbalanceoutletiItem(BaseItem):
    product_id = Field()
    title = Field()
    colors = Field(input_processor=MapCompose(safely_json_loads), output_processor=TakeAll())
    variants = Field(input_processor=MapCompose(variants_processor), output_processor=TakeAll(), skip=True)
    prices = Field(output_processor=TakeAll(), default=list(), skip=True)
    list_prices = Field(output_processor=TakeAll(), default=list(), skip=True)
    skus = Field(output_processor=skus_processor, order=1)
    stock = Field(output_processor=chain_all, skip=True)
    color_images = Field(output_processor=color_images_processor, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=1)
    features = Field(output_processor=TakeAll())
    description = Field(input_processor=MapCompose(format_html_string))
