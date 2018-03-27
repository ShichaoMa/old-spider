# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
"""
item的建立
1 所有item的公共父类为BaseItem。用来提供最基本的信息，base item必须继承， child item可以不继承。
2 item中定义所有item属性prop = Field(...)。
3 Field定义如下：
  1）input_processor: processor函数，参见https://docs.scrapy.org/en/latest/topics/loaders.html#input-and-output-processors
  2）output_processor：默认为TakeFirst()，可以重写该processor。
  3) default：当prop值为空时为该字段提供默认值。
  4）order：对prop进行排序，有些prop依赖于之前的prop，这种情况下，对这两个属性进行排序是有必要的，默认order=0。
  5）skip: 是否在item中略过此prop，默认skip=False。
"""
import re

from functools import partial
from scrapy import Item, Field
from scrapy.loader.processors import MapCompose

from toolkit import rid


class BaseItem(Item):
    domain = Field()
    crawlid = Field()
    spiderid = Field()
    response_url = Field()
    status_code = Field()
    status_msg = Field()
    url = Field()
    seed = Field()
    timestamp = Field()
    meta = Field()
    fingerprint = Field()
    item_type = Field()
    proxy = Field()
    part_number = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))
    mpn = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))
    model_number = Field(input_processor=MapCompose(partial(rid, old=re.compile(r"[^a-zA-Z0-9]"), new="")))
