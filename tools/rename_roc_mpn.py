# -*- coding:utf-8 -*-
import re
import pdb
import json
import psycopg2

from scrapy import Selector

conn = psycopg2.connect(database="roc_production", user="postgres", password="postgres", host="192.168.200.152", port="5432")

cursor = conn.cursor()

print("Success")

cursor.execute("select max(id) from parent_wares;")
total = cursor.fetchone()[0]
print(total)


def amazon(doc):
    sel = Selector(text=doc["product_specifications"])
    model_number = "".join(sel.xpath('//th[contains(text(), "Model number")]/following-sibling::td/text()').extract()).strip()
    part_number = "".join(sel.xpath('//th[contains(text(), "Part")]/following-sibling::td/text()').extract()).strip()
    return model_number, part_number, part_number


def jomashop(doc):
    return re.search(r"Item No\. (.*)", doc["product_ids"]).group(1), re.search(r"Item No\. (.*)", doc["product_ids"]).group(1), re.search(r"Item No\. (.*)", doc["product_ids"]).group(1)


def jacobtime(doc):
    return doc["product_id"], doc["product_id"], doc["product_id"]


def ashford(doc):
    return doc["product_id"], doc["product_id"], doc["product_id"]


def areatrend(doc):
    if doc.get("ware"):
        return doc["ware"][0]["style"], doc["ware"][0]["style"], doc["ware"][0]["style"]
    else:
        if "detail" in doc:
            sel = Selector(text=doc["detail"])
            style = "".join(sel.xpath('//td[@data-th="Style"]/text()').extract()).strip()
            return style, style, style
        return None, None, None


def certifiedwatchstore(doc):
    return doc["product_id"], doc["product_id"], doc["product_id"]


callbacks = {
    "amazon": (1, amazon),
    "jomashop": (8, jomashop),
    "jacobtime": (9, jacobtime),
    "ashford": (10, ashford),
    "areatrend": (100, areatrend),
    "certifiedwatchstore": (98, certifiedwatchstore),
}


def start(source_site):
    source_site_id, callback = callbacks[source_site]
    for i in range(0, total, 10000):
        print("Start to enrich parent_ware from %s to %s"%(i, i+10000))
        cursor.execute("select id, raw from parent_wares where source_site_id=%s and id between %s and %s;", (source_site_id, i, i+10000))
        
        for index, (id, raw) in enumerate(cursor.fetchall()):
            model_number, part_number, mpn = callback(json.loads(raw)["doc"])
            if model_number or part_number or mpn:
                print(id, i, index, model_number, part_number, mpn)
                cursor.execute("update wares set mpn=%s, model_number=%s, part_number=%s where parent_ware_id=%s", (mpn, model_number, part_number, id))
                conn.commit()


if __name__ == "__main__":
    import sys
    start(sys.argv[1])
