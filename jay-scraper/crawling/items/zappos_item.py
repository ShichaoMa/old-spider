# -*- coding: utf-8 -*-
from scrapy import Field
from scrapy.loader.processors import MapCompose, Join
from toolkit import re_search, chain_all, format_html_string, safely_json_loads

from . import BaseItem
from ..utils import TakeAll


def product_id_processor(values, loader_context):
    return loader_context["item"]["productId"]


def color_images_processor(body, loader_context):
    colorIds = loader_context["item"]["colorIds"]
    positions = ['p', '1', '2', '3', '4', '5', '6']
    all_images = {}

    for one_colorId in colorIds.keys():
        for one_position in positions:
            reg_str = r"pImgs\[%s\]\[\'4x\'\]\[\'%s\'\] = . filename: '(.*?)'," % (one_colorId, one_position)
            url = re_search(reg_str, body[0], dotall=False)
            if url:
                all_images.setdefault(one_colorId, []).append(url)
    return all_images


def image_urls_processor(value, loader_context):
    return chain_all(loader_context["item"]["color_images"].values())


def description_processor(value):
    return value.replace("""<li>This product may have a manufacturer's warranty. Pdescription_processorlease visit the
    manufacturer's website or contact us at <a href="mailto:warranty@support.zappos.com">warranty@support.zappos.com</a>
    for full manufacturer warranty details.</li>""", "")


class ZapposItem(BaseItem):
    productId = Field()
    product_id = Field(output_processor=product_id_processor, order=1)
    title = Field(output_processor=Join())
    productDescription = Field(input_processor=MapCompose(format_html_string, description_processor))
    stockJSON = Field(input_processor=MapCompose(safely_json_loads),
                      output_processor=TakeAll(), default=list())
    dimensions = Field(input_processor=MapCompose(safely_json_loads))
    dimToUnitToValJSON = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    dimensionIdToNameJson = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    valueIdToNameJSON = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    colorNames = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    colorPrices = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    styleIds = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    colorIds = Field(input_processor=MapCompose(safely_json_loads), default=dict())
    color_images = Field(output_processor=color_images_processor, default=dict(), order=1)
    image_urls = Field(output_processor=image_urls_processor, default=list(), order=2)
    availability = Field()

