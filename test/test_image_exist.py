# -*- coding:utf-8 -*-

from pymongo import MongoClient

conn = MongoClient("192.168.200.120", 27017)

db = conn["products"]

col = db["jay_loco_amazons"]

rs = col.find({"crawlid": "5116"}, {"images": 1})

for i in rs:

    print(i)