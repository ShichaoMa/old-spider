import re
import json

from urllib.parse import urljoin
from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class ClarksusaPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("_A"))

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
        title = self.enrich_bullet(spu_id, item["title"], "title")
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        for color_meta in item["colors"]:
            color = self.enrich_dimension(spu_id, "color", color_meta["color_id"], color_meta["color"])
            for size_id, size in color_meta["sizes"].items():
                size = self.enrich_dimension(spu_id, "size", size_id, size)
                package["references"].append(size)
                for width_id, sku_meta in color_meta["availabilities"][size_id].items():
                    width = self.enrich_dimension(spu_id, "width", width_id, color_meta["widths"][width_id])
                    package["references"].append(width)
                    steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                  total_albums[color_meta["color_id"]], [specs, title, description], color, size, width)
                    dyno_info = self.enrich_dyno_info(color_meta["price"], 0, not sku_meta["outOfStock"],
                        "Out of stock" if sku_meta["outOfStock"] else "In stock", 5, "USD")
                    sku = self.enrich_sku(spu_id, sku_meta["url"].split("/")[-1], item["status_code"], item["meta"]["tags"],
                        item["timestamp"], urljoin(item["url"], sku_meta["url"]), dyno_info, steady_info)
                    package["references"].append(sku)
                    skus.append(sku)
            package["references"].append(color)
        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(description)
        return skus


class ClarksusaKafkaPipeline(ClarksusaPipelineAdapter, KafkaPipeline):
    pass


class ClarksusaFilePipeline(ClarksusaPipelineAdapter, FilePipeline):
    pass

