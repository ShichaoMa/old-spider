import re
import json

from toolkit import re_search
from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class EzcontactsPipelineAdapter(BaseAdapter):


    @staticmethod
    def get_type(image_block, regex=re.compile(r"_([A-Z])\.jpg")):
        return re_search(regex, image_block, default="MAIN")

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
        for sku_id, sku in item["product"]["allOptionsData"].items():
            color_name = sku.pop("color")
            color_id = item["product"]["colorOptions"][color_name]["id"]
            color = self.enrich_dimension( spu_id, "color", color_id, color_name)
            size_name = sku.pop("size")
            size = self.enrich_dimension(spu_id, "size", size_name, size_name)
            package["references"].append(size)
            package["references"].append(color)
            dyno_info = self.enrich_dyno_info(
                sku.pop("actualPrice") or item["price"],
                sku.pop("price") or item["list_price"],
                True, sku.pop("availability"), 5, "USD")
            sku.pop("rotate360", None)
            sku.pop("rotate360Prefix", None)
            sku.pop("sort_order", None)
            specs = self.enrich_bullet(
                spu_id,
                json.dumps([(k.replace("_", ""), "Yes" if v is True else v) for k, v in sku.items() if v]),
                "specs")
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"],
                                                  item["part_number"], total_albums[color_id],
                                                  [specs, title], color, size)
            sku = self.enrich_sku(spu_id, sku_id, item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
            package["references"].append(specs)
        package["references"].append(title)
        return skus


class EzcontactsKafkaPipeline(EzcontactsPipelineAdapter, KafkaPipeline):
    pass


class EzcontactsFilePipeline(EzcontactsPipelineAdapter, FilePipeline):
    pass

