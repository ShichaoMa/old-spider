import json
import datetime

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter


class VictoriassecretPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block["key"].count("_F.jpg"))

    @staticmethod
    def position(image_block):
        return "https://dm.victoriassecret.com/%s/760x1013/%s.jpg" % (
            'p' if image_block['image'].count('tif/') else 'product', image_block.get("image"))

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
        features = self.enrich_bullet(spu_id, json.dumps(item["features"]), "features")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        for price_meta in item["price_info"]:
            for s in price_meta["sizeCode"]:
                size = self.enrich_dimension(spu_id, "size", "", s)
                package["references"].append(size)
                for c in price_meta["colorCode"]:
                    color = self.enrich_dimension(spu_id, "color", c, item["selector"].get(c, c))
                    package["references"].append(color)
                    availability_reason = "In stock"
                    availability = True
                    stock = 5
                    for st in item["stock_info"]:
                        if st[0] == price_meta["itemNbr"] and st[1] == s and st[2] == c:
                            if st[3] == "B":
                                d = datetime.datetime.fromtimestamp(int(st[4]))
                                availability_reason = "Estimated Ship %s/%s" % (d.month, d.day)
                                availability = True
                            elif st[3] == "D":
                                availability_reason = "Out of stock"
                                availability = False
                                stock = 0
                            elif st[3] == "L":
                                availability_reason = "In Stock. Just a Few Left."
                                availability = True
                                stock = int(st[5])
                            else:
                                continue
                            break
                    steady_info = self.enrich_steady_info("", price_meta["itemNbr"], price_meta["itemNbr"],
                                                          price_meta["itemNbr"], total_albums[c],
                                                          [description, title, features], size, color)
                    dyno_info = self.enrich_dyno_info(price_meta["origPrice"], price_meta["salePrice"], availability,
                                                      availability_reason, stock, "USD")
                    sku = self.enrich_sku(spu_id, "%s_%s_%s" % (price_meta["itemNbr"], c, s), item["status_code"],
                                          item["meta"]["tags"], item["timestamp"], item["url"], dyno_info, steady_info)
                    package["references"].append(sku)
                    skus.append(sku)
        package["references"].append(description)
        package["references"].append(title)
        package["references"].append(features)
        return skus


class VictoriassecretKafkaPipeline(VictoriassecretPipelineAdapter, KafkaPipeline):
    pass


class VictoriassecretFilePipeline(VictoriassecretPipelineAdapter, FilePipeline):
    pass

