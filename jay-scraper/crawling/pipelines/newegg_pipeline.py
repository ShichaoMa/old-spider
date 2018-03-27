import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class NeweggPipelineAdapter(BaseAdapter):

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)\.jpg")):
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
        for sku in (item["skus"] or [item]):
            description = self.enrich_bullet(spu_id, sku["description"], "desc")
            specs = self.enrich_bullet(spu_id, json.dumps(sku["specs"]), "specs")
            title = self.enrich_bullet(spu_id, sku["title"], "title")
            color = self.enrich_dimension(spu_id, "color", sku["color_id"], sku["color"])
            size = self.enrich_dimension(spu_id, "size", sku["size_id"], sku["size"])
            width = self.enrich_dimension(spu_id, "width", "", sku["width"])
            package["references"].append(color)
            package["references"].append(size)
            package["references"].append(width)
            steady_info = self.enrich_steady_info("", sku["model_number"], sku["mpn"], sku["part_number"],
                          total_albums[sku["color"] or "init"], [description, title, specs], color, size, width)
            dyno_info = self.enrich_dyno_info(format_price(sku["price"]), format_price(sku["list_price"]),
                                              True, "In stock" if sku["stock"] else "Out of stock", sku["stock"], "USD")
            sku = self.enrich_sku(spu_id, sku["sku_id"], item["status_code"], item["meta"]["tags"],
                                  sku["timestamp"], sku["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
            package["references"].append(description)
            package["references"].append(title)
            package["references"].append(specs)
        return skus


class NeweggKafkaPipeline(NeweggPipelineAdapter, KafkaPipeline):
    pass


class NeweggFilePipeline(NeweggPipelineAdapter, FilePipeline):
    pass

