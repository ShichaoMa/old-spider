# -*- coding:utf-8 -*-
from requests import get
from scrapy import Selector
#import pymongo
from urllib.parse import urljoin
#import pdb

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    "Accept-Language": "en-US,en;q=0.5",
    "Cookie": "D_ZID=BD763E80-80C7-3BE6-8945-E553C4FB1029;D_SID=23.83.236.209:UrJdaeCr0OXNj8YS4rPJGGgSy06q86mWo2sbfA1lbrg;D_UID=F1FBDFB9-DEF1-32D4-8299-4F784475575A;D_IID=939D1695-634B-356A-B981-8ACEE26C1FC4;D_HID=TgwvBOECiSZjP2tULaaRUypFxBrZ0rmSTEeGsHUfx4A;D_PID=3119DF0B-3C06-308A-88B4-6118E4B86D16;"
}

proxies = {"http": "http://192.168.200.90:8123"}
#
# client = pymongo.MongoClient("192.168.200.120")
#
# db = client["products"]
#
# col = db["jay_amazon_updates"]
#
# rs = col.find({}, {"asin": 1})
#
# count = 0
#
# #for item in rs:
# print(count +1, "B011Z7IZA8", end=":")
# #resp = get("http://upcdeal.us/products.php?q=%s"%item["asin"], headers=headers)
# resp = get("http://upcdeal.us/amazonpro.php?nodatakk=100&upc=887439815289", headers=headers)
# print(resp.headers)
# print(resp.status_code)
# pdb.set_trace()
# sel = Selector(text = resp.text)
# upc = sel.xpath('//strong/text()')
# print("".join(upc.extract()))
# count += 1

def get_site_by_upc(upc):

    url = "http://upcdeal.us/products.php?k=%s&rand=%s"%(upc, upc)
    resp = get(url, headers=headers, proxies=proxies)
    sel = Selector(text=resp.text)
    next_url = urljoin(url, "".join(sel.re(r'var _0x23ef=\["(.*?)"')))
    print(next_url)
    next_resp = get(next_url, headers=headers, proxies=proxies)
    sel = Selector(text=next_resp.text)
    #pdb.set_trace()
    sites = [site.strip(" Logo").lower() for site in sel.xpath("//tr/td/a/img/@alt").extract()]
    urls = [urljoin(url, path)for path in sel.xpath("//tr/td/a/img/../@href").extract()]
    option_urls = []
    for child in urls:
        resp_child = get(url=child, headers=headers, proxies=proxies)
        option_urls.append(resp_child.url)
    print(dict(zip(sites, option_urls)))

if __name__ == "__main__":
    get_site_by_upc("886678124701")