import json

from toolkit import chain_all, custom_re, duplicate

from . import KafkaPipeline
from .formatter import Formatter


class NoneRemoveList(list):

    def append(self, p_object):
        if p_object is not None:
            super(NoneRemoveList, self).append(p_object)


class AmazonPipeline(KafkaPipeline, Formatter):

    def __init__(self, settings):
        KafkaPipeline.__init__(self, settings)
        Formatter.__init__(self)

    def process_item(self, item, spider):

        package = self.get_package()
        package["trace"] = self.enrich_trace()
        references = NoneRemoveList()
        spu_id = "%s#%s" % (item["meta"].get("source_site_code"), item["product_id"])
        total_images = list()
        total_albums = dict()
        for color, images in item["color_images"].items():
            imgs = list()
            for image in images:
                imgs.append(self.enrich_image(
                    spu_id, color, image["hiRes"],
                    self.gen_path(self.settings.get("IMAGE_STORE", "http://192.168.200.71:8888/"), image["hiRes"]),
                    image["variant"] == "MAIN", image["variant"]))
            total_images.append(imgs)
            total_albums[color] = self.enrich_album(spu_id, color, *imgs)
        references.extend(chain_all(total_images))
        references.extend(total_albums.values())
        skus, titles, specs, descriptions, features = list(), list(), list(), list(), list()
        for sku_id, sku in item["skus"].items():
            if item["dimensions_display"]:
                labels = dict(zip(item["dimensions_display"], item["variations_data"].get(sku_id)))
                size = self.enrich_dimension(spu_id, "size", "", labels.get("Size"))
                color = self.enrich_dimension(spu_id, "color", "", labels.get("Color"))
            else:
                labels, size, color = None, None, None
            title = self.enrich_bullet(spu_id, sku["title"], "title")
            titles.append(title)
            feature = self.enrich_bullet(spu_id, sku["feature"], "features",
                                         convert=lambda string: json.dumps(custom_re(r"<span>(.*?)</span>", string)))
            features.append(feature)
            description = self.enrich_bullet(spu_id, sku["product_description"], "desc")
            descriptions.append(description)
            spec = self.enrich_bullet(spu_id, sku["product_specifications"], "specs",
                                      convert=lambda string: json.dumps(custom_re(r"<tr><th>(.*?)</th><td>(.*?)</td></tr>", string)))
            specs.append(spec)
            price = sku.get("price", sku.get("from_price")) or (sku["other"] and sku["other"][0].get("price")) or 0

            dyno_info = self.enrich_dyno_info(price, sku.get("list_price"), sku["availability"],
                                             sku["availability_reason"], sku["stock"], sku["currency"])
            steady_info = self.enrich_steady_info(
                "", item["model_number"], item["mpn"], item["part_number"],
                total_albums[labels and labels.get("Color") or "initial"], [title, feature, description, spec], size, color)
            sku = self.enrich_sku(spu_id, sku_id, item["status_code"], item["meta"]["tags"], sku["timestamp"], sku["url"], dyno_info, steady_info)
            references.append(size)
            references.append(color)
            references.append(sku)
            skus.append(sku)
        references.extend(chain_all([duplicate(titles, key=lambda title: title["item_id"]),
                                     duplicate(features, key=lambda feature: feature["item_id"]),
                                     duplicate(descriptions, key=lambda description: description["item_id"]),
                                     duplicate(specs, key=lambda spec: spec["item_id"])]))
        package["references"] = references
        spu = self.enrich_item(spu_id, item["meta"], item["status_code"], *skus)
        package["items"] = [spu]
        open("test.json", "w").write(__import__("json").dumps(package, indent=1))

        return super(AmazonPipeline, self).process_item(package, spider)