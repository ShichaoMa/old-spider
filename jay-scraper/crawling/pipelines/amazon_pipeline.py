import json

from toolkit import custom_re

from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import SafeSet


class AmazonPipelineAdapter(BaseAdapter):
    @staticmethod
    def is_main(image_block):
        return image_block["variant"] == "MAIN"

    @staticmethod
    def position(image_block):
        return image_block["hiRes"]

    @staticmethod
    def get_type(image_block):
        return image_block["variant"]

    @staticmethod
    def choice(name, nums):
        return_val = ""
        for n, num in nums.items():
            return_val = num or return_val
            if n == name and num:
                return_val = num
                break
        return return_val

    def process_custom(self, spu_id, total_albums, package, item):
        """
        主要用来获取bullet和skus
        :param spu_id:
        :param total_albums:
        :param package:
        :param item:
        :return:
        """
        skus, titles, specs, descriptions, features = list(), list(), list(), list(), list()
        for sku_id, sku in item["skus"].items():
            labels = dict(zip(item["dimensions_display"], item["variations_data"].get(sku_id, [])))
            size = self.enrich_dimension(spu_id, "size", "", labels.get("Size", labels.get("Größe")))
            color_names = SafeSet()
            if "Color" in labels:
                c = labels.get("Color")
                color_sub_name = labels.get("Lens Color")
                if color_sub_name:
                    color_names.add(c + " " + color_sub_name)
                else:
                    color_names.add(c)
            if "Farbe" in labels:
                color_names.add(labels.get("Farbe"))
            if "Band Color" in labels:
                color_names.add(labels.get("Band Color"))
            color_name = color_names.pop()
            color = self.enrich_dimension(spu_id, "color", "", color_name)
            bullets = []
            if sku["title"]:
                titles.append(self.enrich_bullet(spu_id, sku["title"], "title"))
                bullets.append(titles[-1])
            if sku["feature"]:
                features.append(
                    self.enrich_bullet(spu_id, sku["feature"], "features",
                    convert=lambda string: json.dumps(custom_re(r"<span>(.*?)</span>", string))))
                bullets.append(features[-1])
            if sku["product_description"]:
                descriptions.append(self.enrich_bullet(spu_id, sku["product_description"], "desc"))
                bullets.append(descriptions[-1])
            if sku["product_specifications"]:
                specs.append(self.enrich_bullet(spu_id, json.dumps(sku["product_specifications"]), "specs"))
                bullets.append(specs[-1])
            price = sku.get("price", sku.get("from_price")) or (sku["other"] and sku["other"][0].get("price")) or 0
            dyno_info = self.enrich_dyno_info(price, sku.get("list_price"), sku["availability"],
                                             sku["availability_reason"], sku["stock"], sku["currency"])
            nums = {"model_number":  sku["model_number"], "mpn": sku["mpn"], "part_number": sku["part_number"]}
            album = total_albums.get(color_name or "initial")
            if not album and "initial" in total_albums:
                album = total_albums.get("initial")
            steady_info = self.enrich_steady_info("", self.choice("model_number", nums), self.choice("mpn", nums),
                                                  self.choice("part_number", nums), album, bullets, size, color)
            sku = self.enrich_sku(
                spu_id, sku_id, item["status_code"], item["meta"]["tags"],
                sku["timestamp"], sku["url"], dyno_info, steady_info)
            package["references"].append(size)
            package["references"].append(color)
            package["references"].append(sku)
            skus.append(sku)
        package["references"].extend(titles)
        package["references"].extend(features)
        package["references"].extend(descriptions)
        package["references"].extend(specs)
        return skus


class AmazonKafkaPipeline(AmazonPipelineAdapter, KafkaPipeline):
    pass


class AmazonFilePipeline(AmazonPipelineAdapter, FilePipeline):
    pass
