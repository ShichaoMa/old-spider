import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class JomashopPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return not bool(image_block.count("_"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)\.jpg")):
        return re_search(regex, image_block, default="MAIN")

    def process_custom(self, spu_id, total_albums, package, item):
        skus = list()
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        title = self.enrich_bullet(spu_id, item["product_name"], "title")
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        steady_info = self.enrich_steady_info(item["upc"], item["model_number"], item["mpn"], item["part_number"],
                                              total_albums["init"], [specs, title, description])
        dyno_info = self.enrich_dyno_info(format_price(item["final_price"]), format_price(item["retail_price"]),
                                          item["availability"], item["availability_reason"], 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
                              item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(description)
        return skus


class JomashopKafkaPipeline(JomashopPipelineAdapter, KafkaPipeline):
    pass


class JomashopFilePipeline(JomashopPipelineAdapter, FilePipeline):
    pass

