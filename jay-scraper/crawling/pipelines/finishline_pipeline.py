import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price, SafeList


class FinishlinePipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("P1"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_([A-Z0-9]+?)\?")):
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
        description = self.enrich_bullet(spu_id, item["productDescription"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        for color_id, color in item["colors"].items():
            color = self.enrich_dimension(spu_id, "color", color_id, color)
            for size in item["sizes"]["sizes_%s"%color_id]:
                id, value = size.popitem()

                size = self.enrich_dimension(spu_id, "size", id, value.replace("unavailable", "").strip())
                package["references"].append(size)
                steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                              total_albums[color_id.replace("-", "_")], [description, title], size, color)
                prices = SafeList(item["prices"]["prices_%s"%color_id])
                availability = not bool(value.count("unavailable"))
                dyno_info = self.enrich_dyno_info(format_price(prices.pop()), format_price(prices.pop()), availability,
                                                  *("In stock", 5) if availability else ("Out of stock", 0), "USD")
                sku = self.enrich_sku(spu_id, id, item["status_code"], item["meta"]["tags"],
                    item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                skus.append(sku)
            package["references"].append(color)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class FinishlineKafkaPipeline(FinishlinePipelineAdapter, KafkaPipeline):
    pass


class FinishlineFilePipeline(FinishlinePipelineAdapter, FilePipeline):
    pass

