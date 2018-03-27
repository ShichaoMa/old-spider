import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class EccoPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("01_"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"/(\d+)_")):
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
        title = self.enrich_bullet(spu_id, item["title"], "title")
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        for color_id, color_meta in item["colors"].items():
            color = self.enrich_dimension(spu_id, "color", color_id, color_meta["color"])
            package["references"].append(color)
            if color_meta["sizes"]:
                for size_meta in color_meta["sizes"]:
                    size = self.enrich_dimension(spu_id, "size", "", size_meta[0])
                    package["references"].append(size)
                    steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                  total_albums[color_id], [description, title, features], size, color)
                    dyno_info = self.enrich_dyno_info(
                        format_price(color_meta["sales_price"]), format_price(color_meta["standard_price"]),
                        True, size_meta[1], 5 if size_meta[1] else 0, "USD")
                    sku = self.enrich_sku(spu_id, "%s_%s"%(color_id, size_meta[0]), item["status_code"], item["meta"]["tags"],
                        item["timestamp"], item["url"], dyno_info, steady_info)
                    package["references"].append(sku)
                    skus.append(sku)
            else:
                steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                      total_albums[color_id], [description, title, features], color)
                dyno_info = self.enrich_dyno_info(
                    format_price(color_meta["sales_price"]), format_price(color_meta["standard_price"]),
                    True, "In stock", 5, "USD")
                sku = self.enrich_sku(spu_id, color_id, item["status_code"], item["meta"]["tags"],
                                      item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                skus.append(sku)
        package["references"].append(description)
        package["references"].append(features)
        package["references"].append(title)
        return skus


class EccoKafkaPipeline(EccoPipelineAdapter, KafkaPipeline):
    pass


class EccoFilePipeline(EccoPipelineAdapter, FilePipeline):
    pass

