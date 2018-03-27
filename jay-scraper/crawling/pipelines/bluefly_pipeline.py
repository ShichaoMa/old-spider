import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class BlueflyPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return BlueflyPipelineAdapter.get_type(image_block) == "MAIN"

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        return re_search(regex, image_block, default="MAIN")

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
        for color_meta in item["colors"]:
            color = self.enrich_dimension(spu_id, "color", "", color_meta["color"])
            title = self.enrich_bullet(spu_id, color_meta["title"], "title")
            features = self.enrich_bullet(spu_id, json.dumps(color_meta["features"]), "features")
            package["references"].append(color)
            package["references"].append(features)
            package["references"].append(title)
            for sku in color_meta["skus"]:
                for v in sku["options"][0]["values"]:
                    if v["isSelected"]:
                        size = self.enrich_dimension(spu_id, "size", v["value"], color_meta["sizes"][v["value"]])
                        package["references"].append(size)
                steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                              total_albums[color_meta["color_id"]], [title, features], size, color)
                dyno_info = self.enrich_dyno_info(sku["price"].get("salePrice", sku["price"]["price"]),
                                                  sku["price"]["msrp"],
                                                  sku["inventoryInfo"]["manageStock"], "",
                                                  sku["inventoryInfo"]["onlineStockAvailable"], "USD")
                sku = self.enrich_sku(spu_id, sku["variationProductCode"], item["status_code"], item["meta"]["tags"],
                    item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                skus.append(sku)
        return skus


class BlueflyKafkaPipeline(BlueflyPipelineAdapter, KafkaPipeline):
    pass


class BlueflyFilePipeline(BlueflyPipelineAdapter, FilePipeline):
    pass

