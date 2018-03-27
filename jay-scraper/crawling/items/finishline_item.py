# -*- coding: utf-8 -*-
import re
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, chain_all, re_search

from . import BaseItem
from ..utils import TakeAll


# https://www.finishline.com/store/rwd/product/womens-adidas-pureboost-x-element-running-shoes/prod2771599?responsive=true&styleId=BB6088&colorId=ASH
# https://www.finishline.com/store/rwd/product/mens-adidas-originals-relaxed-plus-strapback-hat/prod2767692?responsive=true&styleId=CI4280&colorId=NVY
# 上面两个商品的图片链接不太一样，新修复的正则支持上面两种图片
def image_urls_processor(values, loader_context):
    colors = loader_context["item"]["colors"]
    color_ids = [color_id.replace("-", "_") for color_id in colors.keys()]
    return chain_all([re.sub(r"(?<=/)(\w+_\w+)(?=_\w+)", color_id,
                             "https:%s" % value.replace("\r\n", "").replace("https:", ""))
                      for value in values] for color_id in color_ids)


def color_images_processor(values, loader_context):
    color_images = dict()
    image_urls = loader_context["item"]["image_urls"]
    regex = re.compile(r"(?<=/)(\w+_\w+)(?=_\w+)")
    for image_url in image_urls:
        color_images.setdefault(re_search(regex, image_url), []).append(image_url)
    return color_images


class FinishlineItem(BaseItem):
    product_id = Field()
    title = Field()
    productDescription = Field(input_processor=MapCompose(format_html_string))
    color_images = Field(output_processor=color_images_processor, order=2, default=dict())
    image_urls = Field(output_processor=image_urls_processor, order=1, default=list())
    prices = Field(default=dict())
    colors = Field(default=dict())
    sizes = Field(default=dict())