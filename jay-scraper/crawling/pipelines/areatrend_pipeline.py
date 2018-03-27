import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class AreatrendPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return AreatrendPipelineAdapter.get_type(image_block) == "MAIN"

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        return re_search(regex, image_block, default="MAIN")

    def process_custom(self, spu_id, total_albums, package, item):
        description = self.enrich_bullet(spu_id, item["description"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        specs = self.enrich_bullet(spu_id, json.dumps(item["specs"]), "specs")
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")

        if item["skus"].get("attributes"):
            skus = self.do_multi(spu_id, package, item, [specs, title, description, features], total_albums)
        else:
            skus = self.do_single(spu_id, package, item, [specs, title, description, features], total_albums)

        package["references"].append(specs)
        package["references"].append(title)
        package["references"].append(features)
        package["references"].append(description)
        return skus

    def do_multi(self, spu_id, package, item, bullets, total_albums):
        skus = dict()
        has_size = False

        for option in item["skus"]['attributes'].get("131", dict()).get("options", []):
            color = self.enrich_dimension(spu_id, "color", option["id"], option["label"])
            for product in option["products"]:
                skus.setdefault(product, dict())["color"] = color

        for option in item["skus"]['attributes'].get("132", dict()).get("options", []):
            has_size = True
            size = self.enrich_dimension(spu_id, "size", option["id"], option["label"])
            for product in option["products"]:
                skus.setdefault(product, dict())["size"] = size

        sku_list = list()
        for sku_id, sku in skus.items():
            color = sku.get("color")
            size = sku.get("size")
            if has_size and not (color and size):
                continue
            package["references"].append(color)
            package["references"].append(size)
            prices = item["skus"]['optionPrices'][sku_id]
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                  total_albums[item["skus"]['index'][sku_id]["131"]],
                                                  bullets, size, color)
            dyno_info = self.enrich_dyno_info(prices["oldPrice"]["amount"], prices["finalPrice"]["amount"],
                                              item["availability"] or False, "In stock", 5, "USD")
            sku = self.enrich_sku(spu_id, sku_id, item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            sku_list.append(sku)
        return sku_list

    def do_single(self, spu_id, package, item, bullets, total_albums):
        steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                              total_albums["init"], bullets)
        dyno_info = self.enrich_dyno_info(format_price(item["special_price"]), format_price(item["old_price"]),
                                          item["availability"] or False, "In stock", 5, "USD")
        sku = self.enrich_sku(spu_id, spu_id.split("#")[-1], item["status_code"], item["meta"]["tags"],
                              item["timestamp"], item["url"], dyno_info, steady_info)
        package["references"].append(sku)
        return [sku]


class AreatrendKafkaPipeline(AreatrendPipelineAdapter, KafkaPipeline):
    pass


class AreatrendFilePipeline(AreatrendPipelineAdapter, FilePipeline):
    pass

