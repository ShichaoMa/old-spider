import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class AshfordPipelineAdapter(BaseAdapter):

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
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        title = self.enrich_bullet(spu_id, item["prodName"], "title")
        description = self.enrich_bullet(spu_id, item["prod_desc"], "desc")
        condition = item["condition"]
        if condition:
            condition_detail, condition = condition, "special"
        else:
            condition_detail, condition = "", "new"
        steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                      total_albums["init"], [specs, title, description],
                                              condition=condition, condition_detail=condition_detail)
        dyno_info = self.enrich_dyno_info(item["Your_price"], item["sale_price"],
                                          item["availability"], item["availability_reason"], 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
            item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(description)
        return skus


class AshfordKafkaPipeline(AshfordPipelineAdapter, KafkaPipeline):
    pass


class AshfordFilePipeline(AshfordPipelineAdapter, FilePipeline):
    pass

