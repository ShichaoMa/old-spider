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
from scrapy import Field
from scrapy.loader.processors import MapCompose
from toolkit import format_html_string, safely_json_loads, duplicate

from . import BaseItem


def image_urls_processor(values):
    return duplicate(value['hires'] for value in values)


def colors_processor(values):
    return [value['title'] for value in values]


class NixonItem(BaseItem):
    product_id = Field()
    part_number = Field()
    spec = Field(input_processor=MapCompose(format_html_string))
    title = Field()
    feature = Field(input_processor=MapCompose(format_html_string))
    price = Field(default="$0")
    image_urls = Field(input_processor=MapCompose(safely_json_loads), output_processor=image_urls_processor, default=list())
    colors = Field(input_processor=MapCompose(safely_json_loads), output_processor=colors_processor, default=list())
