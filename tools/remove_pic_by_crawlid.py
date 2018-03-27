# -*- coding:utf-8 -*-
import os
import glob
from pymongo import MongoClient

conn = MongoClient("192.168.200.120")

db = conn["products"]

col = db["jay_amazons"]


def main(crawlid):
    rs = col.find({"crawlid": crawlid}, {"images": 1})

    for item in rs:
        for image in item["images"]:
            for img in glob.glob("%s/*"%os.path.dirname(image["path"])):
                if img != image["path"] and img.endswith("jpg"):
                    os.system("rm -rf %s"%img)
                    print(img)


if __name__ == "__main__":

    cs = """201504270089
201702160002
201702160003
201702160004
201702160006
201702160008
201505040057
"""
    for c in cs.split("\n"):
        if c:
            main(c)