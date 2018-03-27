import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class CertifiedwatchstorePipelineAdapter(BaseAdapter):

    @staticmethod
    def get_type(image_block, regex=re.compile(r"/(\w+)\.jpg")):
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

        steady_info = self.enrich_steady_info(item["upc"], item["model_number"], item["mpn"], item["part_number"],
                      total_albums["init"], [description, title])
        dyno_info = self.enrich_dyno_info(item["special_price"], item["msr_price"],
                                          item["availability"], item["availability_reason"], item["stock"], "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
            item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        skus.append(sku)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class CertifiedwatchstoreKafkaPipeline(CertifiedwatchstorePipelineAdapter, KafkaPipeline):
    pass


class CertifiedwatchstoreFilePipeline(CertifiedwatchstorePipelineAdapter, FilePipeline):
    pass

