# -*- coding:utf-8 -*-
import json
import time
import requests

import asyncio
def crawl():

    resp = requests.post("http://0.0.0.0:9999/api/discover",
                         data={"data": json.dumps({"crawlid": "roc_%s"%time.strftime("%Y%m%d%H%M%S"),
                         "source_site_code": "FFCHCN", "full": True,
                         "url": "https://www.farfetch.cn/cn/shopping/men/buckled-shoes-2/items.aspx",
                         "meta": {"tags": {"source_site_code": "FFCHCN", "tags": [], "brand_id": 1,
                                           "gender_id": 1, "source_site_id": 1, "taxon_id": 3}}})})

    print(resp.text)
# class ApiTest(unittest.TestCase):
#
#     def test_feed(self):
#         self.assertEqual()

def tags():

    resp = requests.post("http://192.168.200.31:9999/api/enrich/tags",
                         data={"data": json.dumps({"source_site_code": "AMZN", "type": "ENRICH",
                         "url": "https://www.amazon.com/s/ref=lp_679337011_ex_n_10?rh=n%3A7141123011%2Cn%3A7147440011%2Cn%3A679337011%2Cn%3A6127767011&bbn=679337011&ie=UTF8",
                         "tags": ["aaa"]})})

    print(resp.text)


def update():
    resp = requests.post("http://0.0.0.0:9999/api/update",
                         json={
                         "site": "FFCHCN",
                         "full": True, "messages": [{"tags": [], "item_id": "", "meta": {"url": "https://www.farfetch.cn/cn/shopping/men/asics---item-12527082.aspx?storeid=9671&from=listing"}}]
                         })

    print(resp.text)



#
# update()

