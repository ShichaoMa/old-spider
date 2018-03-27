import re

from toolkit import re_search

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import format_price


class ZapposPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        if isinstance(image_block, dict):
            return image_block["type"] in ["PAIR", "MAIN"]
        return bool(image_block.count("-p-"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"-(\w+)-")):
        if isinstance(image_block, dict):
            return image_block["type"]
        return re_search(regex, image_block)

    @staticmethod
    def position(image_block):
        if isinstance(image_block, dict):
            return "https://m.media-amazon.com/images/I/%s.jpg" % image_block["imageId"]
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
        description = self.enrich_bullet(spu_id, item["productDescription"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        skus = list()
        if item["response_url"].count("luxury"):
            self.do_old(spu_id, total_albums, package, item, skus, description, title)
        else:
            self.do_new(spu_id, total_albums, package, item, skus, description, title)
        package["references"].append(description)
        package["references"].append(title)
        package["references"].extend(skus)
        return skus

    def do_new(self, spu_id, total_albums, package, item, skus, description, title):
        for style in item["product"].get("detail", {}).get("styles", []):
            color = self.enrich_dimension(spu_id, "color", style["colorId"], style["color"])
            for stock in style["stocks"]:
                width = self.enrich_dimension(spu_id, "width", "", stock["width"])
                size = self.enrich_dimension(spu_id, "size", stock["sizeId"], stock["size"])
                dyno_info = self.enrich_dyno_info(
                    format_price(style["price"]), format_price(style["originalPrice"]),
                    *(True, "In stock") if int(stock["onHand"]) else (False, "Out of stock"), int(stock["onHand"]), "USD")
                steady_info = self.enrich_steady_info(stock["upc"], item["model_number"], item["mpn"],
                    item["part_number"], total_albums[style["colorId"]], [description, title], color, width, size)
                sku = self.enrich_sku(spu_id, stock["stockId"], item["status_code"], item["meta"]["tags"],
                                      item["timestamp"], item["url"], dyno_info, steady_info)
                skus.append(sku)
                package["references"].append(width)
                package["references"].append(size)
            package["references"].append(color)

    def do_old(self, spu_id, total_albums, package, item, skus, description, title):
        color_prices = item["colorPrices"]
        color_ids = dict((str(v), k) for k, v in item["colorIds"].items())
        colors = dict()
        for id, color in item["colorNames"].items():
            colors[id] = self.enrich_dimension(spu_id, "color", id, color)
        for stock in item["stockJSON"]:
            dimensions = dict()
            for id, dimension in item["dimensionIdToNameJson"].items():
                if dimension == "size":
                    dimensions[id] = self.enrich_dimension(
                        spu_id, dimension, stock[id], item["valueIdToNameJSON"][stock[id]]["value"])
                break
            price_meta = color_prices[stock["color"]]
            dyno_info = self.enrich_dyno_info(
                price_meta["nowInt"], price_meta["wasInt"],
                *(True, "In stock") if stock["onHand"] else (False, "Out of stock"), stock["onHand"], "USD")
            steady_info = self.enrich_steady_info("", item["model_number"], item["mpn"], item["part_number"],
                total_albums[color_ids[stock["color"]]], [description, title], colors[stock["color"]], *dimensions.values())
            sku = self.enrich_sku(spu_id, stock["id"], item["status_code"], item["meta"]["tags"],
                                  item["timestamp"], item["url"], dyno_info, steady_info)
            skus.append(sku)
            package["references"].extend(dimensions.values())
        package["references"].extend(colors.values())


class ZapposKafkaPipeline(ZapposPipelineAdapter, KafkaPipeline):
    pass


class ZapposFilePipeline(ZapposPipelineAdapter, FilePipeline):
    pass

