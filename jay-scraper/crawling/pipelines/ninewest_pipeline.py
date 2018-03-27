import json

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter, format_price


class NinewestPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(NinewestPipelineAdapter.get_type(image_block).count("right"))

    @staticmethod
    def position(image_block):
        return image_block["url"]

    @staticmethod
    def get_type(image_block):
        return image_block["type"]

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
        for sku in item["skus"]:
            color = self.enrich_dimension(spu_id, "color", sku["variantColor"], item["colors"][sku["variantColor"]])
            width = self.enrich_dimension(spu_id, "width", "", sku["variantWidth"])
            if sku["variantSize"]:
                size = self.enrich_dimension(spu_id, "size", "", str(int(sku["variantSize"])/10) if
                sku["variantSize"].isdigit() else sku["variantSize"])
                package["references"].append(size)
            else:
                size = None
            dyno_info = self.enrich_dyno_info(format_price(sku["sellingPrice"]), format_price(sku["listPrice"]),
                                              sku["inventory"] > 0, sku["inventoryType"], sku["inventory"], "USD")
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                total_albums[sku["variantColor"]], [description, title, features], size, color, width)
            sku = self.enrich_sku(spu_id, sku["ID"], item["status_code"], item["meta"]["tags"],
                item["timestamp"], item["url"], dyno_info, steady_info)
            package["references"].append(sku)
            skus.append(sku)
            package["references"].append(color)
            package["references"].append(width)
        package["references"].append(description)
        package["references"].append(title)
        package["references"].append(features)
        return skus


class NinewestKafkaPipeline(NinewestPipelineAdapter, KafkaPipeline):
    pass


class NinewestFilePipeline(NinewestPipelineAdapter, FilePipeline):
    pass

