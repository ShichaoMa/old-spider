# -*- coding:utf-8 -*-
"""
item的建立
1 所有item的公共父类为BaseItem。用来提供最基本的信息，base item必须继承BaseItem， child item可以不继承于BaseItem。
2 item中定义所有item属性prop = Field(...)。
3 Field定义如下：
  1）input_processor: processor函数，参见https://docs.scrapy.org/en/latest/topics/loaders.html#input-and-output-processors
  2）output_processor：默认为TakeFirst()，可以重写该processor。
  3) default：当prop值为空时为该字段提供默认值。
  4）order：对prop进行排序，有些prop依赖于之前的prop，这种情况下，对这两个属性进行排序是有必要的，默认order=0。
  5）skip: 是否在item中略过此prop，默认skip=False。
"""
import re
import time

from functools import partial
from scrapy import Item, Field
from scrapy.loader.processors import MapCompose, Compose
from toolkit import format_html_string, chain_all, safely_json_loads, rid

from . import BaseItem
from ..utils import TakeAll
from ..pipelines.utils import format_price


def exception_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
    return wrapper


def product_id_processor(value, loader_context):
    return loader_context["item"]["parent_asin"]


def get_the_largest_one_from_images(image):
    big_image = ""
    if "hiRes" in image:
        big_image = image["hiRes"]
    if not big_image and "large" in image:
        big_image = image["large"]
    variant = image.get("variant")
    image.clear()
    image["hiRes"] = big_image
    image["variant"] = variant
    return big_image


def color_images_processor(value):
    return dict((color, [image for image in images]) for color, images in value.items())


def image_urls_processor(value, loader_context):
    color_images = loader_context["item"]["color_images"]
    if isinstance(color_images, dict):
        return [get_the_largest_one_from_images(i) for i in chain_all(color_images.values())]
    else:
        return [get_the_largest_one_from_images(i) for i in color_images]


def shipping_cost_processor(value):
    if "kostenfreie" in value.lower():
        return 0
    if "free" in value.lower():
        return 0
    elif '+' in value:
        try:
            return value
        except Exception:
            from toolkit import debugger
            debugger()
    else:
        return None


def avalibility_processor(values, loader_context):
    reason = loader_context["item"]["availability_reason"].lower()
    have = ["only", 'in stock', 'usually',
            'ships from and sold by',
            u'Auf Lager', u"Nur", u"Gewöhnlich",
            u'Lieferbar', u'在庫', u'残', u'通常']
    return bool([x for x in have if reason.startswith(x.lower())]) or \
           reason.startswith('available from') or \
           reason.startswith("erhältlich")


def stock_processor(values, loader_context):
    mth = re.search(r"(\d*)\D*[iI]n\s[sS]tock", loader_context["item"]["availability_reason"])
    if mth:
        return (mth.group(1) and int(mth.group(1))) or 5
    elif loader_context["item"]["availability"]:
        return 5
    else:
        return 0


class AmazonBaseItem(BaseItem):
    product_id = Field(order=1)
    parent_asin = Field()
    node_ids = Field(output_processor=TakeAll(), default=[])
    similar_node_ids = Field(output_processor=TakeAll(), default=[])
    brand = Field()
    gender = Field()
    dimensions_display = Field(
        input_processor=Compose(MapCompose(partial(safely_json_loads, defaulttype=list))),
        output_processor=TakeAll(), default=list())
    variations_data = Field(input_processor=Compose(
        MapCompose(format_html_string, safely_json_loads), chain_all), default=dict())
    color_images = Field(
        input_processor=MapCompose(exception_wrapper(safely_json_loads),
                                   color_images_processor), default=dict())
    image_urls = Field(output_processor=image_urls_processor, default=[], order=1)
    skus = Field(output_processor=lambda values: dict((value.get("asin"), dict(value)) for value in values),
                 default=dict())


class AmazonSkuItem(Item):
    asin = Field()
    title = Field()
    url = Field()
    timestamp = Field(output_processor=lambda x: time.time())
    product_specifications = Field(output_processor=TakeAll(), default=[])
    product_description = Field(input_processor=MapCompose(format_html_string))
    feature = Field(input_processor=MapCompose(format_html_string))
    price = Field(default=0)
    merchantID = Field()
    from_price = Field(default=0)
    availability_reason = Field()
    currency = Field(default="USD")
    stock = Field(output_processor=stock_processor, order=2, default=0)
    availability = Field(output_processor=avalibility_processor, order=1, default=False)
    list_price = Field(default=0)
    shipping_cost = Field(input_processor=MapCompose(shipping_cost_processor), default=0)
    other = Field(output_processor=TakeAll(), default=[])
    part_number = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))
    mpn = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))
    model_number = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))


class AmazonUpdateItem(AmazonBaseItem, AmazonSkuItem):
    pass
