import re
import json

from toolkit import re_search
from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class NeimanmarcusPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        if isinstance(image_block, dict):
            return bool(image_block["type"].count("m"))
        return bool(image_block.count("_m"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+)")):
        if isinstance(image_block, dict):
            return image_block["type"]
        return re_search(regex, image_block)

    @staticmethod
    def position(image_block):
        if isinstance(image_block, dict):
            return image_block["url"]
        return image_block

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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        for sku in item["skus"]:
            if "color" in sku:
                color_name = sku["color"].split("?")[0]
                color = self.enrich_dimension(spu_id, "color", item["colors"].get(color_name, ""), color_name)
                package["references"].append(color)
            else:
                color = None
            size = self.enrich_dimension(spu_id, "size", "", sku["size"])
            package["references"].append(size)
            dyno_info = self.enrich_dyno_info(
                item["price"], item["price"], bool(sku["stockAvailable"]), sku["status"], sku["stockAvailable"], "USD")
            album = total_albums[item["colors"][color_name] if item["colors"] else "init"]
            steady_info = self.enrich_steady_info(
                "", item["model_number"], item["mpn"], item["part_number"], album, [features, title], color, size)
            sku = self.enrich_sku(
                spu_id, sku["cmosSku"], item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)

        package["references"].append(features)
        package["references"].append(title)
        return skus


class NeimanmarcusKafkaPipeline(NeimanmarcusPipelineAdapter, KafkaPipeline):
    pass


class NeimanmarcusFilePipeline(NeimanmarcusPipelineAdapter, FilePipeline):
    pass

