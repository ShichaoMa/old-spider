import re

from toolkit import re_search
from . import KafkaPipeline, FilePipeline
from .formatter import BaseAdapter
from .utils import References


class EastbayPipelineAdapter(BaseAdapter):

    @staticmethod
    def is_main(image_block):
        return bool(image_block.count("_fr_"))

    @staticmethod
    def get_type(image_block, regex=re.compile(r"_(\w+?)_")):
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
        all_skus = list()
        description = self.enrich_bullet(spu_id, item["INET_COPY"], "desc")
        title = self.enrich_bullet(spu_id, item["title"], "title")
        all_sizes = References([self.enrich_dimension(spu_id, "size", "", size.strip()) for size in
                     item["model"].get("AVAILABLE_SIZES", [])])
        for color_id, color_meta in item["styles"].items():
            color = self.enrich_dimension(spu_id, "color", color_id,
                                          "|".join(filter(None, [color_meta[15], color_meta[17]])))
            width = self.enrich_dimension(spu_id, "width", "", color_meta[16])
            sizes = all_sizes[:]
            skus = []
            for sku in color_meta[7]:
                index = 0
                while sizes:
                    if sizes[index]["value"] == sku[0].strip():
                        size = sizes.pop(index)
                        break
                    index += 1
                else:
                    size = None
                price = float(sku[1])
                list_price = float(sku[2])
                skus.append((price, list_price, True, "In stock", 5, size))
            for size in sizes:
                skus.append((0, 0, False, "Out of stock", 0, size))
            for sku in skus:
                dyno_info = self.enrich_dyno_info(*sku[:-1], "USD")
                steady_info = self.enrich_steady_info(
                    "", item["model_number"], item["mpn"], item["part_number"],
                    total_albums[color_id], [description, title], sku[-1], color, width)
                sku = self.enrich_sku(spu_id, "_".join((color_id, sku[-1]["value"] if sku[-1] else "")), item["status_code"],
                                      item["meta"]["tags"], item["timestamp"], item["url"], dyno_info, steady_info)
                package["references"].append(sku)
                all_skus.append(sku)
            package["references"].append(color)
            package["references"].append(width)
        package["references"].extend(all_sizes)
        package["references"].append(description)
        package["references"].append(title)
        return all_skus


class EastbayKafkaPipeline(EastbayPipelineAdapter, KafkaPipeline):
    pass


class EastbayFilePipeline(EastbayPipelineAdapter, FilePipeline):
    pass

