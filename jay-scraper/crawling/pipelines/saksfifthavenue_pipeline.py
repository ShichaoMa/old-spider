import re
import json

from toolkit import re_search
from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class SaksfifthavenuePipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return SaksfifthavenuePipelineAdapter.get_type(image_block) == "MAIN"

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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        color = self.enrich_dimension(spu_id, "color", "", item["color"])
        for size_id, size_name, aval in item["sizes"]:
            size = self.enrich_dimension(spu_id, "size", size_id, size_name)
            package["references"].append(size)
            avalibility = "unavailable" not in aval
            dyno_info = self.enrich_dyno_info(
                item["price"], item["price"], avalibility,
                *("In stock", 5) if avalibility else ("Out of stock", 0), "USD")
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                  total_albums["init"], [features, title], color, size)
            sku = self.enrich_sku(spu_id, size_id, item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
        if not item["sizes"]:
            dyno_info = self.enrich_dyno_info(item["price"], item["price"], True, "In stock", 5, "USD")
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                  total_albums["init"], [features, title], color)
            sku = self.enrich_sku(spu_id, item["product_id"], item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)

        package["references"].append(color)
        package["references"].append(features)
        package["references"].append(title)
        return skus


class SaksfifthavenueKafkaPipeline(SaksfifthavenuePipelineAdapter, KafkaPipeline):
    pass


class SaksfifthavenueFilePipeline(SaksfifthavenuePipelineAdapter, FilePipeline):
    pass

