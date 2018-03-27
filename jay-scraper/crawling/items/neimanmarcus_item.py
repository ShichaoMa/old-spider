# -*- coding: utf-8 -*-
import re

from functools import partial

from scrapy import Field
from scrapy.loader.processors import MapCompose, Compose
from toolkit import duplicate, chain_all, re_search, safely_json_loads

from . import BaseItem
from ..utils import TakeAll


def image_urls_processor(values, loader_context):
    color_images = loader_context["item"]["color_images"]
    if color_images:
        return [img["url"] for img in chain_all(color_images.values())]
    else:
        return duplicate(values)


def color_images_processor(values):
    color_images = dict()
    regex = re.compile("_(\w+?)_")
    for value in values:
        for t, img_uri in value.items():
            color_images.setdefault(re_search(regex, img_uri), []).append(
                {
                    "type": t,
                    "url": "https://neimanmarcus.scene7.com/is/image/NeimanMarcus/%s?&wid=1200&height=1500" % img_uri
                }
            )
    return color_images


class NeimanmarcusItem(BaseItem):
    product_id = Field()
    title = Field()
    features = Field(output_processor=Compose(partial(filter, lambda x: bool(x.strip())), duplicate))
    skus = Field(output_processor=TakeAll())
    colors = Field(default=dict())
    color_images = Field(
        input_processor=MapCompose(safely_json_loads), output_processor=color_images_processor, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    price = Field()
