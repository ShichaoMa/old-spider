import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class FarfetchPipelineAdapter(BaseAdapter):
    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\d+)\.jpg")):
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
        title = self.enrich_bullet(spu_id, item["title"], "title")
        package["references"].append(title)
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        package["references"].append(features)
        if item["sizes"]:
            for size_info in item["sizes"]:
                price = re_search(r"(¥[\d,]+)", size_info, default=item["price"])
                av_reason = re_search(r"(最.*)", size_info, default="In stock")
                s_id = size_info.replace("-", "").replace(av_reason, "").replace(price, "").strip()
                size = self.enrich_dimension(spu_id, "size", "", s_id)
                package["references"].append(size)
                steady_info = self.enrich_steady_info("", item["model_number"],
                                                      item["mpn"],
                                                      item["part_number"],
                                                      total_albums["init"],
                                                      [features, title], size)
                dyno_info = self.enrich_dyno_info(item["price"], item["price"],
                                                  True, av_reason,
                                                  int(re_search(r"(\d+)", av_reason, default=5)),
                                                  "CNY")
                sku = self.enrich_sku(spu_id, s_id,
                                      item["status_code"], item["meta"]["tags"],
                                      item["timestamp"], item["url"], dyno_info,
                                      steady_info)
                package["references"].append(sku)
                skus.append(sku)
        else:
            steady_info = self.enrich_steady_info("", item["model_number"],
                                                  item["mpn"], item["part_number"],
                                                  total_albums["init"],
                                                  [features, title])
            dyno_info = self.enrich_dyno_info(item["price"], item["list_price"],
                                              True, "In stock", 5, "CNY")
            sku = self.enrich_sku(spu_id, spu_id.split("#")[-1],
                                  item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info,
                                  steady_info)
            package["references"].append(sku)
            skus.append(sku)
        return skus


class FarfetchKafkaPipeline(FarfetchPipelineAdapter, KafkaPipeline):
    pass


class FarfetchFilePipeline(FarfetchPipelineAdapter, FilePipeline):
    pass
