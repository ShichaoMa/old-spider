import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class MonclerPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("_f"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_([a-z]+?)\.")):
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
        for sku in item["skus"]:
            color = self.enrich_dimension(spu_id, "color", sku["colorPartNumber"], sku["productColor"]["identifier"])
            size = self.enrich_dimension(spu_id, "size", "", sku["productSize"]["identifier"])
            package["references"].append(color)
            package["references"].append(size)
            if sku["colorPartNumber"] not in total_albums:
                continue
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                          total_albums[sku["colorPartNumber"]], [description, title], size, color)
            dyno_info = self.enrich_dyno_info(format_price(item["prices"][sku["colorPartNumber"]]), 0, sku["buyable"],
                                              *("In stock", 1) if sku["buyable"] else ("Out of stock", 0), "USD")
            sku = self.enrich_sku(spu_id, sku["skuPartNumber"], item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
            package["references"].append(color)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class MonclerKafkaPipeline(MonclerPipelineAdapter, KafkaPipeline):
    pass


class MonclerFilePipeline(MonclerPipelineAdapter, FilePipeline):
    pass

