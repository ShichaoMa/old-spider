import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class WatchstationPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return WatchstationPipelineAdapter.get_type(image_block) == "main"

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        return re_search(regex, image_block)

    def process_custom(self, spu_id, total_albums, package, item):
        skus = list()
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                              total_albums["init"], [specs, title, description])
        dyno_info = self.enrich_dyno_info(format_price(item["price"]), format_price(item["old_price"]),
                                          True, "In stock", 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
                              item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(description)
        return skus


class WatchstationKafkaPipeline(WatchstationPipelineAdapter, KafkaPipeline):
    pass


class WatchstationFilePipeline(WatchstationPipelineAdapter, FilePipeline):
    pass

