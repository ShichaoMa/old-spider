import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class SsencePipelineAdapter(BaseAdapter):
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
        title = self.enrich_bullet(spu_id, item["title"], "title")
        package["references"].append(title)
        description = self.enrich_bullet(spu_id, item["description"], "description")
        package["references"].append(description)
        for size_id in item["sizes"]:
            size = self.enrich_dimension(spu_id, "size", *size_id.split("_")[::-1])
            package["references"].append(size)
            steady_info = self.enrich_steady_info("", item["model_number"],
                                                  item["mpn"],
                                                  item["part_number"],
                                                  total_albums["init"],
                                                  [title, description], size)
            dyno_info = self.enrich_dyno_info(item["price"], item["price"],
                                              True, "In stock",
                                              5, "CAD")
            sku = self.enrich_sku(spu_id, size_id, item["status_code"],
                                  item["meta"]["tags"], item["timestamp"],
                                  item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)

        return skus


class SsenceKafkaPipeline(SsencePipelineAdapter, KafkaPipeline):
    pass


class SsenceFilePipeline(SsencePipelineAdapter, FilePipeline):
    pass
