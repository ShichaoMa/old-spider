# -*- coding:utf-8 -*-
"""
spider custom pipeline.
"""
import json
import hashlib

from os.path import splitext, basename
from urllib.parse import urlparse
from toolkit import chain_all, duplicate, re_search

from . import KafkaPipeline


class MonclerPipeline(KafkaPipeline):

    def __init__(self, settings):
        super(MonclerPipeline, self).__init__(settings)
        self.new_item = {"version": "0.6"}

    def process_item(self, item, spider):
        new_item = self.new_item.copy()
        new_item["command"] = item["meta"]["type"]
        new_item["trace"] = {
            "app": "jay",
            "spiderid": item["spiderid"],
            "crawlid": item["crawlid"],
            "domain": item["domain"],

            "fingerprint": item["fingerprint"],
            "proxy": item["proxy"],
            "url": item["url"],
            "response_url": item["response_url"],

            "status_code": item["status_code"],
            "status_msg": item["status_msg"],
        }
        _item = dict()
        _item["item_type"] = item["item_type"]
        _item["item_id"] = {"site": item["meta"].get("source_site_code"), "sku": item["product_id"]}
        _item["item_url"] = item["response_url"]
        _item["item_timestamp"] = item["timestamp"]
        _item["item_status_code"] = "NORMAL" if item["status_code"] == 200 else "ERROR"
        _item["meta"] = item["meta"]
        _item["albums"] = dict()

        for color, images in item["color_images"].items():
            for image_url in images:
                filename, file_ext = splitext(basename(urlparse(image_url).path))
                if not file_ext:
                    file_ext = ".jpg"
                else:
                    file_ext = file_ext.lower()
                out_file_name = "%s/%s/%s%s" % (self.settings.get("IMAGES_STORE"), item["spiderid"], hashlib.sha1(
                        image_url.encode("utf-8")).hexdigest(), file_ext)
                _item["albums"].setdefault(color, []).append({'url': image_url, 'path': out_file_name, "origin": True})

        _item["bullets"] = {
            "title": [item["title"]],
            "description": [item["description"]],
            "features": [],
            "spec": []
        }
        colors = [{"id": color["color_id"], "key": color["color_id"], "value": color["color"]} for color in item["colors"]]
        sizes = [{"id": size, "key": size, "value": size}
                 for size in duplicate(chain_all(color["sizes"][1:] for color in item["colors"]))]
        _item["dimentions"] = {
            "color": colors,
            "size": sizes,
            "width": []
        }
        __items = list()
        for color in item["colors"]:
            for index, size in enumerate(color["sizes"][1:]):
                size_no = re_search(r"(\S+)", size)
                sku = dict()
                sku["item_type"] = "ware"
                sku["item_id"] = {"site": item["meta"].get("source_site_code"),
                                  "sku": item["product_id"],
                                  "color": color["color"],
                                  "size": size_no}
                sku["item_url"] = color["url"]
                sku["item_timestamp"] = color["timestamp"]
                sku["item_status_code"] = "NORMAL" if color["status_code"] == 200 else "ERROR"
                sku["meta"] =  {"tags": item["meta"]["tags"]}
                sku["steady_info"] = {
                    "dimentions": {
                        "color": color["color_id"],
                        "size": size_no,
                        "width": ""
                    },

                    "album": color["color"],

                    "bullets": {
                        "title_id": 0,
                        "description_id": 0,
                    },
                    "UPC": "",
                    "ASIN": "",
                    "style_feature": ""
                }
                sku["dyno_info"] = {
                    "price": color["price"],
                    "availability": False if color["availabilities"][index+1].count("Contact me") else True,
                    "availability_reason": "In stock" if color["availabilities"][index+1].count("Contact me") else "Out of stock",
                }
                __items.append(sku)
        _item["items"] = __items
        new_item["items"] = [_item]
        open("test.json", "w").write(json.dumps(new_item, indent=2))
        return super(KenzoPipeline, self).process_item(new_item, spider)