import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class CoachPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("a0"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_([a-z0-9]+?)(?=$)")):
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
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        for color_id, color_meta in item["colors"].items():
            color = self.enrich_dimension(spu_id, "color", color_id, color_meta["color"]["displayValue"])
            if color_meta["size"]:
                for size_meta in color_meta["size"][0]["values"]:
                    size = self.enrich_dimension(spu_id, "size", size_meta["id"], size_meta["displayValue"])
                    package["references"].append(size)
                    steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                  total_albums[color_id.replace("/", "")], [description, title, features], size, color)
                    availability = size_meta["selectable"]
                    dyno_info = self.enrich_dyno_info(format_price(color_meta["sales_price"]), 0, availability,
                                                      *("In stock", 5) if availability else ("Out of stock", 0), "USD")
                    sku = self.enrich_sku(spu_id, "_".join((color_id, size_meta["id"])), item["status_code"], item["meta"]["tags"],
                        item["timestamp"], item["url"], dyno_info, steady_info)
                    package["references"].append(sku)
                    skus.append(sku)
            else:
                steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                      total_albums[color_id.replace("/", "")],
                                                      [description, title, features], color)
                availability = color_meta["color"]["selectable"]
                dyno_info = self.enrich_dyno_info(color_meta["sales_price"], 0, availability,
                                                  *("In stock", 5) if availability else ("Out of stock", 0), "USD")
                sku = self.enrich_sku(spu_id, color_id, item["status_code"], item["meta"]["tags"],
                                      item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                skus.append(sku)
            package["references"].append(color)
        package["references"].append(description)
        package["references"].append(features)
        package["references"].append(title)
        return skus


class CoachKafkaPipeline(CoachPipelineAdapter, KafkaPipeline):
    pass


class CoachFilePipeline(CoachPipelineAdapter, FilePipeline):
    pass

