import time
import copy
from os.path import join
from hashlib import md5, sha1
from functools import reduce


class Formatter(object):
    def __init__(self):
        self.version = "1.1.2"

    @staticmethod
    def md5_encode(string, count=6):
        return md5(string.encode("utf-8")).hexdigest()[:count]

    @classmethod
    def gen_path(cls, base, url):
        codec = cls.sha1_encode(url)
        return join(base, codec[:2], codec[2:4], codec[4:], "%s.jpg"%codec)

    @staticmethod
    def sha1_encode(string):
        return sha1(string.encode("utf-8")).hexdigest()

    def enrich_reference(self, _type, *names):
        reference = dict()
        reference["item_type"] = self.generate_identifier(_type.capitalize(),
                                                          *map(lambda name: name.capitalize(), names))
        return reference

    def enrich_bullet(self, spuid, string, *names, convert=None):
        bullet = self.enrich_reference("bullet", *names)
        bullet["item_id"] = self.generate_identifier(spuid, self.md5_encode(string))
        bullet["en"] = convert(string) if convert else string
        return bullet

    @staticmethod
    def generate_identifier(prefix, *tags):
        return reduce(lambda x, y: "%s::%s" % (x, y), tags, prefix)

    def enrich_album(self, spuid, color, *images):
        album = self.enrich_reference("album")
        album["item_id"] = self.generate_identifier(spuid, color.capitalize())
        album["images"] = self.prop_keeper(images)
        return album

    def enrich_image(self, spuid, color, url, path, main_candidate=False, _type=""):
        image = self.enrich_reference("image")
        image["item_id"] = self.generate_identifier(spuid, color.capitalize(), self.md5_encode(url))
        image["url"] = url
        image["path"] = path
        image["main_candidate"] = main_candidate
        image["type"] = _type
        image["origin"] = True
        return image

    def enrich_dimension(self, spuid, _type, key, value):
        dimension = self.enrich_reference("dimension", _type)
        dimension["item_id"] = self.generate_identifier(spuid, self.md5_encode(value))
        dimension["key"] = key
        dimension["value"] = value
        return dimension

    def enrich_sku(self, spuid, skuid, status_code, tags, timestamp, url, dyno_info, steady_info):
        sku = self.enrich_reference("sku")
        sku["item_id"] = "%s#%s" % (spuid, skuid)
        meta = dict()
        meta["timestamp"] = int(timestamp*1000)
        meta["url"] = url
        sku["tags"] = tags or []
        meta["status_code"] = "NORMAL" if status_code < 300 else "ERROR"
        sku["meta"] = meta
        sku["dyno_info"] = dyno_info
        sku["steady_info"] = steady_info
        return sku

    @staticmethod
    def enrich_dyno_info(price, list_price, availability, availability_reason, stock, currency):
        dyno_info = dict()
        dyno_info["price"] = price
        dyno_info["stock"] = stock
        dyno_info["availability"] = availability and stock > 0
        dyno_info["availability_reason"] = availability_reason
        dyno_info["list_price"] = list_price
        dyno_info["currency"] = currency
        return dyno_info

    def enrich_steady_info(self, upc, model_number, mpn, part_number, album, bullets, *dimensions):
        steady_info = dict()
        steady_info["upc"] = upc
        steady_info["model_number"] = model_number
        steady_info["ean"] = ""
        steady_info["mpn"] = mpn
        steady_info["part_number"] = part_number
        steady_info["condition"] = ""
        steady_info["album"] = self.prop_keeper(album)[0]
        steady_info["dimensions"] = self.prop_keeper(dimensions)
        bts = self.prop_keeper(bullets)
        steady_info["bullets"] = bts
        return steady_info

    @staticmethod
    def prop_keeper(elements, *keys):
        new_elements = list()
        keys = keys or ["item_id", "item_type"]
        for element in elements if isinstance(elements, (list, tuple)) else [elements]:
            if isinstance(element, dict):
                new_element = dict()
                for key in keys:
                    new_element[key] = element[key]
                new_elements.append(new_element)
        return new_elements

    def get_package(self):
        return {"version": self.version, "command": "DISCOVER"}

    @staticmethod
    def enrich_trace():
        return {"app": "jay"}

    def enrich_item(self, spuid, meta, status_code, *skus):
        item = dict()
        item["item_type"] = "Spu"
        item["item_id"] = spuid
        meta["timestamp"] = int(time.time()*1000)
        meta["status_code"] = "NORMAL" if status_code < 300 else "ERROR"
        meta["all_skus"] = True
        item["meta"] = meta
        item["tags"] = meta["tags"] or []
        del meta["tags"]
        item["skus"] = self.prop_keeper(skus)
        return item
