import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class JacobtimePipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return not bool(image_block.count("_"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        return re_search(regex, image_block, default="MAIN")

    def process_custom(self, spu_id, total_albums, package, item):
        skus = list()
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["descript_title"], "title")
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        steady_info = self.enrich_steady_info(item["upc_or_ean"], item["model_number"], item["mpn"], item["part_number"],
                                              total_albums["init"], [specs, title, features])
        dyno_info = self.enrich_dyno_info(format_price(item["your_price"]), format_price(item["retail"]),
                                          item["availability"], item["availability_reason"], 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
                              item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(features)
        return skus


class JacobtimeKafkaPipeline(JacobtimePipelineAdapter, KafkaPipeline):
    pass


class JacobtimeFilePipeline(JacobtimePipelineAdapter, FilePipeline):
    pass

