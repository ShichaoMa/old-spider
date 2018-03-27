import json
from bs4 import BeautifulSoup
import requests
import time
from redis import Redis
from threading import Thread


redis_conn = Redis("192.168.200.150")

proxy_list = redis_conn.lrange("proxy_list", 0, -1)


headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
    }


def do_one_thread(times):

    t0 = time.time()
    for i in range(times):
        t1 = time.time()
        resp = requests.get("https://www.amazon.com/gp/offer-listing/B01NCKWETV/ref=dp_olp_0?ie=UTF8&condition=all",
                            proxies={"https": "https://longen:jinanlongen2016@%s"%proxy_list[i].decode("utf-8")},
                            headers=headers)
        print(resp.status_code, len(resp.text))
        t2 = time.time()
        print("per request cost: ", t2 - t1)
        soup = BeautifulSoup(resp.text, "html")
        prices = [price.get_text() for price in
                  soup.find_all("span", attrs={"class": "a-size-large a-color-price olpOfferPrice a-text-bold"}) +
                  soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row  .a-size-large')]
        shipping_costs = [shipping_cost.get_text() for shipping_cost in
                          soup.select('p[class="olpShippingInfo"]') +
                          soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row p[class="olpShippingInfo"]')]
        merchurts = [merchurt.get_text() for merchurt in soup.select('h3[class="a-spacing-none olpSellerName"] a')]
        buffer = json.dumps(list(zip(prices, shipping_costs, merchurts)))
        print("per parse cost: ", time.time() - t2, buffer)
    print("single cost: ", time.time()-t0)


def do_mutil_thread(times):
    t1 = time.time()
    thread_list = []
    for i in range(times):

        th = Thread(target=get, args=(i, ))
        thread_list.append(th)
        th.start()
    for th in thread_list:
        th.join()
    print("multi cost: ", time.time() - t1)


def get(index):
    t1 = time.time()
    resp = requests.get("https://www.amazon.com/gp/offer-listing/B01NCKWETV/ref=dp_olp_0?ie=UTF8&condition=all",
                        proxies={"https": "https://longen:jinanlongen2016@%s" % proxy_list[index].decode("utf-8")},
                        headers=headers)
    print(resp.status_code, len(resp.text))
    t2 = time.time()
    print("per request cost: ", t2 - t1)
    soup = BeautifulSoup(resp.text, "html")
    prices = [price.get_text() for price in
              soup.find_all("span", attrs={"class": "a-size-large a-color-price olpOfferPrice a-text-bold"}) +
              soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row  .a-size-large')]
    shipping_costs = [shipping_cost.get_text() for shipping_cost in
                      soup.select('p[class="olpShippingInfo"]') +
                      soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row p[class="olpShippingInfo"]')]
    merchurts = [merchurt.get_text() for merchurt in soup.select('h3[class="a-spacing-none olpSellerName"] a')]
    buffer = json.dumps(list(zip(prices, shipping_costs, merchurts)))
    print("per parse cost: ", time.time() - t2, buffer)


def main():
    do_one_thread(10)
    do_mutil_thread(10)


if __name__ == "__main__":
    main()