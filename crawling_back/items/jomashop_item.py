# -*- coding: utf-8 -*-
from scrapy import Field, Selector
from scrapy.loader.processors import MapCompose

from . import BaseItem
from ..utils import re_search, format_html_string


def product_id_processor(values, loader_context):
    return loader_context["item"]["product_ids"]


def image_urls_processor(values, loader_context):
    image_value = loader_context["item"]["image_value"]
    selector = Selector(text=values[0])
    return (lambda urls=selector.xpath(
            '//div[@id="MagicToolboxSelectors%s"]/a/@href|//a[@id="MagicZoomPlusImage%s"]/@href'%(
                image_value, image_value)).extract(): sorted(list(set(urls)), key=urls.index))()


class JomashopItem(BaseItem):
    brand_name = Field()
    product_name = Field()
    product_ids = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    final_price = Field(default="$0")
    retail_price = Field(default="$0")
    savings = Field()
    shipping = Field()
    shipping_availability = Field()
    image_value = Field(skip=True)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=1)
    details = Field(input_processor=MapCompose(format_html_string))
    Color = Field()
    upc = Field()

