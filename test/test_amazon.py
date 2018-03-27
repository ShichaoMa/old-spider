# -*- coding:utf-8 -*-
import os

import requests
import scrapy
import time


def use_requests():
    headers = {
                #'Pragma': 'no-cache',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en',
               #'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               #'Referer': 'https://www.amazon.com/Converse-Unisex-Chuck-Taylor-Sneakers/dp/B0059NGJSU/ref=lp_679260011_1_1?s=apparel&ie=UTF8&qid=1505447322&sr=1-1&nodeID=679260011&psd=1&th=1&psc=1',
               #'Connection': 'keep-alive',
               #'Cache-Control': 'no-cache'
               }

    url = 'https://www.amazon.com/gp/offer-listing/B0064BCJ1M/ref=dp_olp_new_mbc?ie=UTF8&condition=new'

    proxies = {"http": "http://longen:jinanlongen@192.168.17.160:12017"}

    while True:
        resp = requests.get(url, headers=headers, proxies=proxies)
        print(resp.request.headers)
        print(resp.status_code)
        print(len(resp.text))
        open("a.html", "w").write(resp.text)

        # if resp.status_code == 200:
        #     open("a.html", "w").write(resp.text)
        #     break
        time.sleep(1)


def use_curl(url, proxy=None, proxy_auth=None):
    while True:
      time.sleep(1)
      cmd = """curl -o - -s -w "%%{http_code}\n" '%s' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.8,en;q=0.6' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: max-age=0' -H 'Connection: keep-alive' --compressed"""%url
      if proxy:
        cmd += " -x 'http://%s'"%proxy
      if proxy_auth:
        cmd += " -U '%s'"%proxy_auth
      print(cmd)
      return os.popen(cmd).readlines()


if __name__ == "__main__":
    print(use_curl("https://www.amazon.com/gp/offer-listing/B01NCILWOU/ref=dp_olp_0?ie=UTF8&condition=all")[-2:])
    #use_requests()