import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class SwarovskiPipelineAdapter(BaseAdapter):

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)_")):
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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                      total_albums["init"], [features, title, description])
        dyno_info = self.enrich_dyno_info(format_price(item["price"]), format_price(item["price"]),
                                          item["availablity"], item["availablity_reason"], 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
            item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(features)
        package["references"].append(title)
        package["references"].append(description)
        return skus


class SwarovskiKafkaPipeline(SwarovskiPipelineAdapter, KafkaPipeline):
    pass


class SwarovskiFilePipeline(SwarovskiPipelineAdapter, FilePipeline):
    pass

