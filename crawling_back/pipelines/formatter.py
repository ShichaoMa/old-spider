import time
from hashlib import md5
from functools import reduce


class Formatter(object):

    def __init__(self, brands, categories, source_sites, genders):
        self.brands = brands
        self.source_sites = source_sites
        self.genders = genders
        self.categories = categories
        self.version = "1.1.2"
    
    @staticmethod
    def md5_encode(string, count=6):
        return md5(string.encode("utf-8")).hexdigest()[:count]
    
    def enrich_reference(self, _type, *names):
        reference = dict()
        reference["item_type"] = self.generate_identifier(_type.capitalize(), *map(lambda name: name.capitalize(), names))
        return reference
    
    def enrich_bullet(self, spuid, string, *names, enrich=None):
        bullet = self.enrich_reference("bullet", *names)
        bullet["item_id"] = self.generate_identifier(spuid, self.md5_encode(string))
        if enrich:
            enrich(bullet, string)
        else:
            bullet["en"] = string
        return bullet
    
    @staticmethod
    def generate_identifier(prefix, *tags):
        return reduce(lambda x, y: "%s::%s"%(x, y), tags, prefix)

    def enrich_album(self, spuid, color, *images):
        album = self.enrich_reference("album")
        album["item_id"] = self.generate_identifier(spuid, color.capitalize())
        album["images"] = self.prop_filter(images)
        return album
    
    def enrich_image(self, spuid, color, url):
        image = self.enrich_reference("image")
        image["item_id"] = self.generate_identifier(spuid, color.capitalize(), self.md5_encode(url))
        image["url"] = url
        image["type"] = ""
        image["main_candidate"] = True
        image["origin"] = True
        return image
    
    def enrich_dimension(self, spuid, _type, key, value):
        dimension = self.enrich_reference("dimension", _type)
        dimension["item_id"] = self.generate_identifier(spuid, self.md5_encode(value))
        dimension["key"] = key
        dimension["value"] = value
        return dimension
    
    def enrich_sku(self, spuid, skuid, dyno_info, steady_info):
        sku = self.enrich_reference("sku")
        sku["item_id"] = "%s#%s"%(spuid, skuid)
        meta = dict()
        meta["timestamp"] = time.time()
        meta["url"] = ""
        sku["meta"] = meta
        sku["dyno_info"] = dyno_info
        sku["steady_info"] = steady_info
        return sku
    
    @staticmethod
    def enrich_dyno_info(price, stock, list_price):
        dynoInfo = dict()
        dynoInfo["price"] = price
        dynoInfo["stock"] = stock
        dynoInfo["availability"] = stock>0
        dynoInfo["availability_reason"] = ""
        dynoInfo["list_price"] = list_price
        dynoInfo["currency"] = "USD"
        return dynoInfo

    def enrich_steady_info(self, upc, album, bullets, *dimensions):
        steady_info = dict()
        steady_info["upc"] = upc
        steady_info["model_number"] = ""
        steady_info["ean"] = ""
        steady_info["mpn"] = ""
        steady_info["part_number"] = ""
        steady_info["condition"] = ""
        steady_info["album"] = self.prop_filter(album)
        steady_info["dimensions"] = self.prop_filter(dimensions)
        bts = dict((bullet.get("item_type").split("::")[-1].lower(), bullet) for bullet in self.prop_filter(bullets))
        steady_info["bullets"] = bts
        return steady_info

    @staticmethod
    def prop_filter(elements, *keys):
        keys = keys or ["item_id", "item_type"]
        for element in elements:
            for key in keys:
                del element[key]
        return elements

    def get_package(self):
        return {"version": self.version, "command": "DISCOVER" }

    @staticmethod
    def enrich_trace():
        return {"app": "jay"}

    def enrich_item(self, spuid, brand, category, gender, source_site, *skus):
        item = dict()
        item["item_type"] = "Spu"
        item["item_id"] = spuid
        item["skus"] = self.prop_filter(skus)
        meta = dict()
        source_site_code_and_id = self.source_sites.get(source_site)
        meta["source_site_code"] = source_site_code_and_id[0]
        meta["source_site_id"] = int(source_site_code_and_id[1])
        brand_code_and_id = self.brands.get(brand)
        meta["brand_code"] = brand_code_and_id[0]
        meta["brand_id"] = int(brand_code_and_id[1])
        gender_code_and_id = self.genders.get(gender)
        meta["gender_code"] = gender_code_and_id[0]
        meta["gender_id"] = int(gender_code_and_id[1])
        category_code_and_id = self.categories.get(category)
        meta["category_code"] = category_code_and_id[0]
        meta["category_id"] = int(category_code_and_id[1])
        meta["timestamp"] = time.time()
        item["meta"] = meta
        return item
    

   
    

