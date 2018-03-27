import json

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class NordstromPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return image_block["SortId"] == 1

    @staticmethod
    def get_type(image_block):
        return str(image_block["SortId"])

    @staticmethod
    def position(image_block):
        return image_block["ImageMediaUri"]["MaxLarge"]

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
        title = self.enrich_bullet(spu_id, item["product_name"], "title")
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        for sku in item["skus"]:
            color = self.enrich_dimension(spu_id, "color", sku["ColorId"], sku["ColorName"])
            size = self.enrich_dimension(spu_id, "size", sku["SizeId"], sku["Size"])
            width = self.enrich_dimension(spu_id, "size", sku["WidthId"], sku["Width"])
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                                                  total_albums.get(sku["ColorId"]), [description, title, features],
                                                  size, color, width)
            dyno_info = self.enrich_dyno_info(format_price(sku["Price"]), format_price(sku["OriginalPrice"]),
                                              sku["IsAvailable"],
                                              *("In stock", 5) if sku["IsAvailable"] else ("Out of stock", 0), "USD")
            sku = self.enrich_sku(spu_id, sku["Id"], item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
            package["references"].append(width)
            package["references"].append(size)
            package["references"].append(color)
        package["references"].append(features)
        package["references"].append(description)
        package["references"].append(title)
        return skus


class NordstromKafkaPipeline(NordstromPipelineAdapter, KafkaPipeline):
    pass


class NordstromFilePipeline(NordstromPipelineAdapter, FilePipeline):
    pass

