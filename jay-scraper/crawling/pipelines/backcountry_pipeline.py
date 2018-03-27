import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class BackcountryPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return BackcountryPipelineAdapter.get_type(image_block) == "MAIN"

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
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        for sku_id, sku in item["skus_collection"].items():
            _, c_id, s_id = sku_id.split("-")
            c, s = sku["displayName"].split(", ")
            color = self.enrich_dimension(spu_id, "color", c_id, c)
            size = self.enrich_dimension(spu_id, "size", s_id, s)
            package["references"].append(color)
            package["references"].append(size)
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                          total_albums[c_id], [description, title, features, specs], size, color)
            dyno_info = self.enrich_dyno_info(format_price(sku["price"]["low"]), format_price(sku["displayPrice"]),
                                              sku["inventory"] > 0, "In stock" if sku["inventory"] else "Out of stock",
                                              sku["inventory"], "USD")
            sku = self.enrich_sku(spu_id, sku_id, item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
        package["references"].append(features)
        package["references"].append(specs)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class BackcountryKafkaPipeline(BackcountryPipelineAdapter, KafkaPipeline):
    pass


class BackcountryFilePipeline(BackcountryPipelineAdapter, FilePipeline):
    pass

