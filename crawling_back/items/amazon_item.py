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
from functools import partial
from scrapy import Item, Field
from scrapy.loader.processors import MapCompose, Compose

from . import BaseItem
from ..utils import format_html_string, chain_all, safely_json_loads, re_search, TakeAll


def get_the_largest_one_from_images(image):
    big_image = ""
    if "hiRes" in image:
        big_image = image["hiRes"]
    if not big_image and "large" in image:
        big_image = image["large"]
    image.clear()
    image["hiRes"] = big_image
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
        return "EUR 0"
    if "free" in value.lower():
        return "$0"
    elif '+' in value:
        return re_search(r'\+(.*?\d+\.?\d+)', value)
    else:
        return None


def avalibility_processor(value, loader_context):
    reason = loader_context["item"]["availability_reason"].lower()
    have = ["only", 'in stock', 'usually',
            'ships from and sold by',
            u'Auf Lager', u"Nur", u"Gewöhnlich",
            u'Lieferbar', u'在庫', u'残', u'通常']
    if not reason or [x for x in have if reason.startswith(x.lower())]:
        return "true"
    elif reason.startswith('available') or reason.startswith("erhältlich"):
        return "other"
    else:
        return "false"


class AmazonBaseItem(BaseItem):
    product_id = Field(order=1)
    parent_asin = Field()
    node_ids = Field(output_processor=TakeAll(), default=[])
    similar_node_ids = Field(output_processor=TakeAll(), default=[])
    brand = Field()
    gender = Field()
    title = Field()
    product_specifications = Field(input_processor=MapCompose(format_html_string))
    product_description = Field(input_processor=MapCompose(format_html_string))
    feature = Field(input_processor=MapCompose(format_html_string))
    dimensions_display = Field(
        input_processor=Compose(MapCompose(partial(safely_json_loads, defaulttype=list))),
        output_processor=TakeAll())
    variations_data = Field(input_processor=Compose(
        MapCompose(format_html_string, safely_json_loads), chain_all), default=dict())
    color_images = Field(input_processor=MapCompose(safely_json_loads, color_images_processor), default=dict())
    image_urls = Field(output_processor=image_urls_processor, default=[], order=1)
    skus = Field(output_processor=lambda values: dict((value.get("asin"), dict(value)) for value in values),
                 default=dict())


class AmazonSkuItem(Item):
    asin = Field()
    price = Field(default="$0")
    merchantID = Field()
    from_price = Field(default="$0")
    availability_reason = Field()
    availability = Field(output_processor=avalibility_processor, order=1)
    list_price = Field(default="$0")
    shipping_cost = Field(input_processor=MapCompose(shipping_cost_processor), default="$0")
    other = Field(output_processor=TakeAll(), default=[])


class AmazonUpdateItem(AmazonBaseItem, AmazonSkuItem):
    pass
