import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price, SafeList


class KenzoPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("_P_01"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+?)\.")):
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
        for color_meta in item["colors"]:
            color = self.enrich_dimension(spu_id, "color", color_meta["color_id"], color_meta["color"])
            for index in range(1, len(color_meta["sizes"])):
                size = self.enrich_dimension(spu_id, "size", "", color_meta["sizes"][index].split(" ")[0])
                package["references"].append(size)
                steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                              total_albums[color_meta["color"]], [description, title], size, color)
                ab = False if color_meta["availabilities"][index] else True
                dyno_info = self.enrich_dyno_info(format_price(color_meta["price"]), 0, ab,
                                                  color_meta["availabilities"][index] or "in_stock", 1 if ab else 0, "USD")
                sku = self.enrich_sku(spu_id, "%s_%s_%s"%(item["product_id"], color_meta["color_id"], size["value"]),
                                      item["status_code"], item["meta"]["tags"],
                    item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                skus.append(sku)
            package["references"].append(color)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class KenzoKafkaPipeline(KenzoPipelineAdapter, KafkaPipeline):
    pass


class KenzoFilePipeline(KenzoPipelineAdapter, FilePipeline):
    pass

