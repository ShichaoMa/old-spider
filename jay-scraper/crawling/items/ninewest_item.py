# -*- coding:utf-8 -*-
from scrapy import Field
from toolkit import chain_all

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values, loader_context):
    return [value["url"] for value in chain_all(loader_context["item"]["color_images"].values())]


class NinewestItem(BaseItem):
    product_id = Field()
    title = Field()
    features = Field(output_processor=TakeAll())
    description = Field()
    colors = Field(output_processor=dict, default=dict())
    skus = Field(output_processor=TakeAll(), default=dict())
    color_images = Field(output_processor=chain_all, default=dict())
    image_urls = Field(output_processor=image_urls_processor, default=list())
