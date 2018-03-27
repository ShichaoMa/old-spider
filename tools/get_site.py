# -*- coding:utf-8 -*-
import time
import random
import traceback
from psycopg2 import connect
from redis import Redis
from requests import get
from urllib.parse import urljoin
from scrapy import Selector
from queue import Queue, Empty
from threading import Thread, RLock
from multi_thread_closing import MultiThreadClosing

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    "Accept-Language": "en-US,en;q=0.5",
    "Cookie": "D_ZID=BD763E80-80C7-3BE6-8945-E553C4FB1029;D_SID=23.83.236.209:UrJdaeCr0OXNj8YS4rPJGGgSy06q86mWo2sbfA1lbrg;D_UID=F1FBDFB9-DEF1-32D4-8299-4F784475575A;D_IID=939D1695-634B-356A-B981-8ACEE26C1FC4;D_HID=TgwvBOECiSZjP2tULaaRUypFxBrZ0rmSTEeGsHUfx4A;D_PID=3119DF0B-3C06-308A-88B4-6118E4B86D16;"
}

#proxies = {"http": "http://192.168.200.90:8123"}

class GetSite(MultiThreadClosing):

    name = "get_site"

    def __init__(self):
        super(GetSite, self).__init__()
        self.redis_conn = Redis("192.168.200.94")
        self.conn = connect("dbname='upc' user='roc' host='127.0.0.1' password='roc'")
        self.cursor = self.conn.cursor()
        self.queue = Queue()
        self.open()
        self.lock = RLock()
        self.set_logger()
        self.proxy_list = ["http://longen:jinanlongen2016@%s:12017"%x for x in """mh101.headedeagle.com
mh102.headedeagle.com
mh103.headedeagle.com
mh104.headedeagle.com
mh105.headedeagle.com
mh106.headedeagle.com
mh107.headedeagle.com
mh108.headedeagle.com
mh109.headedeagle.com
mh110.headedeagle.com
mh111.headedeagle.com
mh126.headedeagle.com
mh127.headedeagle.com
mh128.headedeagle.com
mh131.headedeagle.com
mh132.headedeagle.com
mh133.headedeagle.com
mh134.headedeagle.com
mh135.headedeagle.com
mh136.headedeagle.com
mh138.headedeagle.com
mh139.headedeagle.com
mh141.headedeagle.com
mh142.headedeagle.com
mh143.headedeagle.com
mh144.headedeagle.com
mh200.headedeagle.com
192.168.11.160
192.168.12.160
192.168.13.160
192.168.14.160
192.168.15.160
192.168.16.160
192.168.17.160
192.168.18.160
mx11.headedeagle.com
mx12.headedeagle.com
mx13.headedeagle.com
mx14.headedeagle.com
mx21.headedeagle.com
mx22.headedeagle.com
mx23.headedeagle.com
mx24.headedeagle.com
""".split("\n")]

    def main(self):
        for i in range(30):
            th = Thread(target=self.process)
            th.start()
            self.threads.append(th)
        self.cursor.execute("select upc, ean, mpn from amazon_roc where upc != '';")
        for i in self.cursor.fetchall():
            upc, ean, mpn = i
            if self.redis_conn.sismember("site_check_set", upc):
                self.logger.info("The upc %s have processed. "%upc)
                continue
            self.logger.debug("Put %s in queue. "%upc)
            self.queue.put(i)
            time.sleep(1)

        while self.alive or [thread for thread in self.threads if thread.is_alive()]:
            time.sleep(1)

    def process(self):
        while self.alive:
            try:
                upc, ean, mpn = self.queue.get_nowait()
                self.logger.debug("Process %s. " % upc)
                while True:
                    try:
                        ean_n, mpn_n, site_urls = self.get_site_by_upc(upc)
                        break
                    except Exception:
                        self.logger.error("Error in get_site_by_upc %s, retry" % traceback.print_exc())
                        time.sleep(1)
                ean_new = ean or ean_n
                mpn_new = mpn or mpn_n
                if ean_new != ean and mpn_new != mpn:
                    self.logger.debug("Update ean %s to %s and mpn %s to %s. " % (ean, ean_new, mpn, mpn_new))
                    with self.lock:
                        try:
                            self.cursor.execute("update anazon_roc set ean=%s, mpn=%s where upc=%s;",
                                           (ean_new, mpn_new, upc))
                            self.conn.commit()
                        except Exception:
                            self.logger.error("Error in update amazon_roc: %s"%traceback.format_exc())
                            self.conn.rollback()
                for site, url in site_urls:
                    if site == "amazon":
                        continue
                    self.logger.debug("Insert %s of %s into site_roc table. " % (url, site))
                    with self.lock:
                        try:
                            self.cursor.execute("insert into site_roc(upc, site, url) values(%s, %s, %s)", (upc, site, url))
                            self.conn.commit()
                        except Exception:
                            self.logger.error("Error in insert site_roc: %s" % traceback.format_exc())
                            self.conn.rollback()
                self.redis_conn.sadd("site_check_set", upc)
            except Empty:
                time.sleep(1)

    def get_site_by_upc(self, upc):
        proxy = {"http": random.choice(self.proxy_list)}
        #self.logger.debug("Proxy: %s"%proxy)
        url = "http://upcdeal.us/products.php?k=%s&rand=%s" % (upc, upc)
        resp = get(url, headers=headers, proxies=proxy)
        sel = Selector(text=resp.text)
        ean = "".join(sel.re(r"EAN.*?:([\d\s]+)")).replace(" ", "")
        #self.logger.debug("New ean: %s"%ean)
        mpn = "".join(sel.re(r"MPN\s*?:([^<]+)")).strip()
        #self.logger.debug("New mpn: %s"%mpn)
        next_url = urljoin(url, "".join(sel.re(r'var _0x\w+?=\["(.*?)"')[:1]))
        if next_url == url:
            self.logger.info("Nothing found. ")
            return ean, mpn, []
        self.logger.debug("Next site_url: %s"%next_url)
        next_resp = get(next_url, headers=headers, proxies=proxy)
        sel = Selector(text=next_resp.text)
        sites = [site.replace(" Logo", "").lower() for site in sel.xpath("//tr/td/a/img/@alt").extract()]
        urls = [urljoin(url, path) for path in sel.xpath("//tr/td/a/img/../@href").extract()]
        option_urls = []
        for child in urls:
            try:
                resp_child = get(url=child, headers=headers, proxies=proxy)
                option_urls.append(resp_child.url)
            except Exception as e :
                self.logger.error("Error in child request: %s, put the raw url. "%e)
                option_urls.append(child)
        return ean, mpn, zip(sites, option_urls)


if __name__ == "__main__":
    GetSite().main()
    #main()
    #print(get_site_by_upc("098689945392"))