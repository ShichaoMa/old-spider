import re
import json

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class SevenforallmankindPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("_l"))

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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        color = item["colors"][0]
        color = self.enrich_dimension(spu_id, "color", color["Id"], color["ColorName"])
        package["references"].append(color)
        sizes = dict((size["Id"], self.enrich_dimension(spu_id, "size", size["Id"], size["SizeName"])) for size in item["size"])
        package["references"].extend(sizes.values())
        for sku in item["sku"]:
            size = sizes[sku["ProductSize"]["Id"]]
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                          total_albums[color["key"]], [description, title, features], size, color)
            dyno_info = self.enrich_dyno_info(
                sku["SalePrice"] or sku["Price"], sku["RegularPrice"], True, "In stock", 5, "USD")
            sku = self.enrich_sku(spu_id, "%d%d" % (sku["ProductColor"]["Id"], sku["ProductSize"]["Id"]),
                                  item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
        package["references"].append(description)
        package["references"].append(features)
        package["references"].append(title)
        return skus


class SevenforallmankindKafkaPipeline(SevenforallmankindPipelineAdapter, KafkaPipeline):
    pass


class SevenforallmankindFilePipeline(SevenforallmankindPipelineAdapter, FilePipeline):
    pass

