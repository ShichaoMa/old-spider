#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import re
import argparse

from redis import Redis
from threading import Thread

import requests


headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        "Accept-Language": "en-US,en;q=0.5",
    }


def start(proxy, url, redis_conn):
    # opener = build_opener(ProxyHandler({"http": proxy}))
    # req = Request(url=url, headers=headers)
    try:
        # print("proxy: %s"%proxy, "response code: %s"%opener.open(req, timeout=30).code)
        resp = requests.get(url, headers=headers, timeout=10, proxies={"http": proxy})
        print("proxy: %s"%proxy, "resposne code: %s"%resp.status_code)
        print("IP: %s, Real IP: %s"%re.search(r'"ip": "(.*?)"[\s\S]+"ip-real": "(.*?)",', resp.text).groups())
        if resp.status_code == 200:
            proxy = proxy.split("@")[-1].encode("utf-8")
            redis_conn.sadd("proxy_set", proxy)
            redis_conn.lpush(proxy, *([""]*10))
            redis_conn.ltrim(proxy, 0, 9)
        else:
            print("not good proxy: %s" % proxy)
    except Exception as e:
        print(e)
        print("not good proxy: %s"%proxy)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-rh", "--redis-host", default="192.168.200.150")
    parser.add_argument("-rp", "--redis-port", type=int, default=6379)
    parser.add_argument("-u", "--url", default="http://www.whatismyip.com.tw/")
    parser.add_argument("-plk", "--proxy-set-key", default="proxy_set")
    parser.add_argument("-pl", "--proxy-list", default="proxy.list")
    args = parser.parse_args()
    redis_conn = Redis(args.redis_host, args.redis_port)
    proxy_set = redis_conn.smembers(args.proxy_set_key)
    for proxy in proxy_set:
        if redis_conn.keys(proxy):
            for i in range(10):
                redis_conn.lset(proxy, i, "")
    redis_conn.delete(args.proxy_set_key)
    with open(args.proxy_list) as f:
        for proxy in ["http://longen:jinanlongen2016@%s:12017"%line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]:
            #start(proxy, args.url, redis_conn)
            t = Thread(target=start, args=(proxy, args.url, redis_conn))
            t.start()


if __name__ == "__main__":
    main()
