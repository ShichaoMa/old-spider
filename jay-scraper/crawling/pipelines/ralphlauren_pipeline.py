import re

from toolkit import re_search
from functools import reduce

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class RalphlaurenPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("standard"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        return re_search(regex, image_block)

    def process_custom(self, spu_id, total_albums, package, item):
        """
        主要用来获取bullet和skus
        :param spu_id:
        :param total_albums:
        :param package:
        :param item:
        :return:
        """
        skus = list()
        description = self.enrich_bullet(spu_id, item["detail"], "desc")
        title = self.enrich_bullet(spu_id, item["product_name"], "title")
        for sku in item["skus"]:
            color = self.enrich_dimension(spu_id, "color", sku["color_id"], sku["color"])
            size = self.enrich_dimension(spu_id, "size", "", sku["size"])
            width = self.enrich_dimension(spu_id, "width", "", sku["width"])
            package["references"].append(size)
            package["references"].append(width)
            package["references"].append(color)
            color_id = sku["color_id"]
            if not color_id and sku["color"]:
                color_id = reduce(lambda x, y: y if y["color"] == sku["color"] else x,
                                  item["skus"], {"color_id": ""})["color_id"]
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                          total_albums.get(color_id), [description, title], size, color, width)
            avalibility = not sku["status"] or "in stock" in sku["status"]
            stock = 5 if avalibility else 0
            dyno_info = self.enrich_dyno_info(sku["price"], sku["standard_price"],
                                              avalibility, sku["status"], stock, "USD")
            sku = self.enrich_sku(spu_id, sku["id"], item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class RalphlaurenKafkaPipeline(RalphlaurenPipelineAdapter, KafkaPipeline):
    pass


class RalphlaurenFilePipeline(RalphlaurenPipelineAdapter, FilePipeline):
    pass

