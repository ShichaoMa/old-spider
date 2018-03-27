import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class JoesnewbalanceoutletPipelineAdapter(BaseAdapter):

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_([0-9]+?)_")):
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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        colors = dict()
        for color in item["colors"]:
            colors[color["c"]] = self.enrich_dimension(spu_id, "color", color["c"], color["v"])
        package["references"].extend(colors.values())
        for sku in item["skus"]:
            color = colors[sku["c"]]
            size = self.enrich_dimension(spu_id, "size", "", [i for i in sku["a"] if i["n"] == "size"][0]["v"])
            width = self.enrich_dimension(spu_id, "size", "", [i for i in sku["a"] if i["n"] == "width"][0]["v"])
            package["references"].append(size)
            package["references"].append(width)
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                          total_albums[sku["c"]], [description, title, features], size, color, width)
            dyno_info = self.enrich_dyno_info(sku["price"], format_price(sku["list_price"]), sku["stock"] > 0,
                                              "In stock" if sku["stock"] > 0 else "Out of stock", sku["stock"], "USD")
            sku = self.enrich_sku(spu_id, sku["v"], item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
        package["references"].append(description)
        package["references"].append(features)
        package["references"].append(title)
        return skus


class JoesnewbalanceoutletKafkaPipeline(JoesnewbalanceoutletPipelineAdapter, KafkaPipeline):
    pass


class JoesnewbalanceoutletFilePipeline(JoesnewbalanceoutletPipelineAdapter, FilePipeline):
    pass

