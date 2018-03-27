import time
import traceback

from os.path import join
from hashlib import md5, sha1
from functools import reduce
from abc import ABC, abstractmethod

from toolkit import chain_all
from toolkit.managers import ExceptContext

from .utils import format_price, References


class Formatter(ABC):
    def __init__(self, *args, **kwargs):
        super(Formatter, self).__init__(*args, **kwargs)
        self.version = "1.0.0"

    @property
    @abstractmethod
    def settings(self):
        pass

    @staticmethod
    def md5_encode(string, count=6):
        return md5(str(string).encode()).hexdigest()[:count]

    @classmethod
    def gen_path(cls, base, spiderid, url):
        codec = cls.sha1_encode(url)
        return join(base, spiderid, "%s.jpg" % codec)

    @staticmethod
    def sha1_encode(string):
        return sha1(string.encode()).hexdigest()

    def enrich_reference(self, _type, *names):
        reference = dict()
        reference["item_type"] = self.generate_identifier(_type.capitalize(), *map(lambda name: name.capitalize(), names))
        return reference

    def enrich_bullet(self, spu_id, string, *names, convert=None):
        bullet = self.enrich_reference("bullet", *names)
        bullet["item_id"] = self.generate_identifier(spu_id, self.md5_encode(string))
        bullet["en"] = convert(string) if convert else string
        return bullet

    @staticmethod
    def generate_identifier(prefix, *tags):
        return reduce(lambda x, y: "%s::%s" % (x, y), tags, prefix)

    def enrich_album(self, spu_id, color, *images):
        album = self.enrich_reference("album")
        album["item_id"] = self.generate_identifier(spu_id, color.capitalize())
        album["images"] = self.prop_keeper(images)
        return album

    def enrich_image(self, spu_id, color, url, path, init=False, _type=""):
        image = self.enrich_reference("image")
        image["item_id"] = self.generate_identifier(spu_id, color.capitalize(), _type or self.md5_encode(url))
        image["url"] = url
        image["path"] = path
        image["init"] = init
        image["type"] = _type
        image["origin"] = True
        return image

    def enrich_dimension(self, spu_id, _type, key, value):
        if not (key or value):
            return None
        dimension = self.enrich_reference("dimension", _type)
        dimension["item_id"] = self.generate_identifier(spu_id, self.md5_encode(value))
        dimension["key"] = key
        dimension["value"] = value
        return dimension

    def enrich_sku(self, spu_id, sku_id, status_code, tags, timestamp, url, dyno_info, steady_info):
        sku = self.enrich_reference("sku")
        sku["item_id"] = "%s#%s" % (spu_id, sku_id)
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
        dyno_info["list_price"] = format_price(list_price)
        dyno_info["price"] = format_price(price) or dyno_info["list_price"]
        dyno_info["stock"] = stock
        dyno_info["availability"] = bool(dyno_info["price"] and availability and stock > 0)
        dyno_info["availability_reason"] = availability_reason
        dyno_info["currency"] = currency
        return dyno_info

    def enrich_steady_info(self, upc, model_number, mpn, part_number, album, bullets, *dimensions,
                           condition="new", condition_detail=""):
        steady_info = dict()
        steady_info["upc"] = upc
        steady_info["model_number"] = model_number
        steady_info["ean"] = ""
        steady_info["mpn"] = mpn
        steady_info["part_number"] = part_number
        steady_info["condition"] = condition
        steady_info["condition_detail"] = condition_detail
        if album:
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

    def enrich_spu(self, spu_id, meta, status_code, *skus):
        item = dict()
        item["item_type"] = "Spu"
        item["item_id"] = spu_id
        meta["timestamp"] = int(time.time()*1000)
        meta["status_code"] = "NORMAL" if status_code < 300 else "ERROR"
        meta["all_skus"] = True
        item["meta"] = meta
        item["tags"] = meta["tags"] or []
        del meta["tags"]
        item["skus"] = self.prop_keeper(skus)
        return item


class BaseAdapter(Formatter):
    settings = None
    logger = None

    @staticmethod
    def is_main(image_block):
        return False

    @staticmethod
    def get_type(image_block):
        return ""

    @staticmethod
    def position(image_block):
        return image_block

    @abstractmethod
    def process_custom(self, spu_id, total_albums, package, item):
        return []

    def log_err(self, func_name, *args):
        self.logger.error("Error in %s: %s. "%(func_name, "".join(traceback.format_exception(*args))))
        return True

    def process_item(self, item, spider):
        if item["product_id"] or item["meta"].get("item_id"):
            with ExceptContext(errback=self.log_err) as ec:
                package = self.get_package()
                package["command"] = item["meta"].pop("type", "DISCOVER")
                package["trace"] = self.enrich_trace()
                package["trace"]["seed"] = item["seed"]
                package["trace"]["proxy"] = item["proxy"]
                package["trace"]["crawlid"] = item["crawlid"]
                package["trace"]["fingerprint"] = item["fingerprint"]
                references = References()
                spu_id = item["meta"].get("item_id") or "%s#%s" % (item["meta"].get("source_site_code"), item["product_id"])
                total_images = list()
                total_albums = dict()
                color_images = item.get("color_images") or {"init": item["image_urls"]}
                for color_id, images in color_images.items():
                    imgs = References()
                    got_main = False
                    first = None
                    for image_block in images:
                        is_main = self.is_main(image_block)
                        got_main = got_main or is_main
                        image = self.enrich_image(spu_id, str(color_id), self.position(image_block), self.gen_path("/",
                        item["spiderid"], self.position(image_block)), is_main, self.get_type(image_block))
                        imgs.append(image)
                        first = first or image
                    if not got_main and first:
                        first["init"] = True
                    total_images.append(imgs)
                    total_albums[color_id] = self.enrich_album(spu_id, str(color_id), *imgs)
                references.extend(chain_all(total_images))
                references.extend(total_albums.values())
                package["references"] = references
                item["meta"]["url"] = item["response_url"]
                spu = self.enrich_spu(
                    spu_id, item["meta"], item["status_code"], *self.process_custom(spu_id, total_albums, package, item))
                package["items"] = [spu]
                item = super(BaseAdapter, self).process_item(package, spider)
            if ec.got_err:
                spider.crawler.stats.set_failed_download(
                    meta=item, reason=traceback.format_exception(*ec.err_info), _type="pipeline")
        else:
            self.logger.error("Item haven't got a product id, url: %s" % item["url"])
        return item
