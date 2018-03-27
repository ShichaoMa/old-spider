# -*- coding:utf-8 -*-
import re
import os
import time
import socket
import random
import traceback

from urllib import quote
from scrapy import Selector
from Queue import Queue, Empty
from threading import Thread, current_thread, RLock
from urllib2 import Request, build_opener, URLError, ProxyHandler

from log_to_kafka import Logger

from utils import get_rex_pat, xpath_exchange, LazyFile


class Crawler(Logger):

    name = "jd_crawler"
    lock = RLock()

    def __init__(self, settings, keyword, num, id, dbconn=None):

        super(Crawler, self).__init__(settings)
        self.keyword = keyword
        self.page_num = int(num)
        self.id = id
        self.dbconn = dbconn
        self.opener = build_opener()
        self.item_queue = Queue()
        self.rex_pat = get_rex_pat(self.settings.get("KEYWORDS"))
        if not os.path.exists("task"):
            os.mkdir("task")
        self.product_file = open("task/where_%s.txt" % id, "w")
        self.keywords_file = LazyFile.open("task/keywords_%s.txt" % id, "w")

    def send_request(self, req):

        while True:
            try:
                proxy = self.get_proxy()
                if proxy:
                    self.opener.add_handler(ProxyHandler({"http": proxy, "https": proxy}))
                return self.opener.open(req, timeout=self.settings.get("TIMEOUT")).read()

            except URLError:
                self.logger.error(traceback.format_exc())
                self.logger.error("将非法代理 %s放到暂存列表中"%proxy)
                self.settings.get("INVALIDATE_PROXY")[proxy] = time.time()
            except socket.timeout:
                time.sleep(0.1)

    def get_proxy(self):
        self.lock.acquire()
        proxy = random.choice(self.settings.get("PROXY_LIST"))

        while proxy in self.settings.get("INVALIDATE_PROXY") and self.settings.get("INVALIDATE_PROXY").get(
                proxy) > time.time() - 60 * 60:
            if len(self.settings.get("INVALIDATE_PROXY")) == len(self.settings.get("PROXY_LIST")):
                proxy = None
                break
            proxy = random.choice(self.settings.get("PROXY_LIST"))

        if proxy in self.settings.get("INVALIDATE_PROXY"):
            del self.settings.get("INVALIDATE_PROXY")[proxy]
        self.lock.release()
        return proxy

    def manage_title_list(self, title_list, thread_list):
        while [x for x in thread_list if x.is_alive()]:
            time.sleep(1)

        keyword = self.keyword.decode("utf-8")
        titles = "".join(title_list)
        new_line = re.sub(r"%s|"%keyword + self.rex_pat, "", titles)
        print(new_line, file=self.keywords_file)
        self.keywords_file.close()
        self.product_file.close()
        self.logger.info("%s task finished. "%self.id)

    def start(self):
        keyword_p = quote(self.keyword)
        first_url = self.settings.get("URL_PATTERN") % keyword_p
        next_queue = [first_url]
        # 京东url中对应的参数s
        s = 0
        # 第几个商品
        count = 1
        # 总页数 与显示页数是2倍的关系
        pages = 0
        # 当前页数
        current_pages = 1
        title_list = []
        thead_list = [Thread(target=self.parse_item, args=(current_thread(), title_list)) for i in range(10)]

        for t in thead_list:
            t.start()

        while next_queue:
            try:
                req = Request(next_queue.pop(0), headers=self.settings.get("HEADERS"))
                sel = Selector(text=self.send_request(req))
                items = sel.xpath('//div[@class="gl-i-wrap"]')

                if req.get_full_url() == first_url:
                    page_content = "".join(sel.xpath('//div[@ id="J_topPage" ]/span/i/text()').extract())
                    pages = int(page_content)
                    pages = min(pages, self.page_num*2)
                    self.logger.debug("发现 %s 页商品。"% (pages/2))
                    self.logger.debug("准备抽取第%s页%s个商品"%((current_pages/2), len(items)*2))

                for item in items:
                    self.item_queue.put((count, item))
                    count += 1

                if current_pages < pages+1:
                    current_pages += 1
                    s += 1
                    next_queue.append(self.settings.get("SEARCH_URL")%(keyword_p, current_pages, s))
            except Exception:
                self.logger.error(traceback.format_exc())

        Thread(target=self.manage_title_list, args=(title_list, thead_list)).start()

    def parse_item(self, current_t, title_list):
        while current_t.is_alive() or not self.item_queue.empty():
            try:
                count, item = self.item_queue.get_nowait()
                self.logger.debug("提取第%s个商品的信息"%count)

                if "".join(item.xpath('div[@class="p-icons"]').extract()).count(u"自营") > 0:
                    i = self.extract_zhiying(count, item)
                else:
                    i = self.extract_else(count, item)
                title_list.append(i["title"])

            except Empty:
                time.sleep(1)
            except Exception:
                self.logger.debug(traceback.format_exc())

    def get_price(self, sku):
        # url = price_url%sku
        # req = Request(url=url, headers=HEADERS)
        # while True:
        #     data = send_request(req)
        #     try:
        #         return json.loads(data)[0]['p']
        #     except KeyError:
        #         pass
        return 0

    def extract_else(self, count, item):
        i = dict()
        i["order"] = count
        i["shopid"] = xpath_exchange(item.xpath('.//div[@class="p-shop"]/@data-shopid'))
        i["shop"] = xpath_exchange(item.xpath('.//div[@class="p-shop"]/span/a/text()'))
        i["price"] = xpath_exchange(item.xpath('.//div[@class="p-price"]/strong/*/text()'))
        i["title"] = xpath_exchange(item.xpath('.//div[@class="p-name p-name-type-2"]/a/@title'))
        item_url = item.xpath('.//div[@class="p-img"]/a/@href').extract()[0].strip()

        try:
            i["sku"] = re.search(r"/(\d+)\.html", item_url).group(1)
        except AttributeError:
            i["sku"] = None

        if not (i["title"] and i["price"] and (i["shopid"] or i["shop"])):

            if not item_url.startswith("http"):
                item_url = "https:%s"%item_url

            req = Request(url=item_url, headers=self.settings.get("HEADERS"))
            sel = Selector(text=self.send_request(req).decode("gbk", "ignore").encode("utf-8"))
            i["shop"] = i["shop"] or xpath_exchange(sel.xpath('//div[@class="name"]/a/@title'))
            i["shopid"] = i["shopid"] or "".join(sel.re(r"shopId:'(\d+?)'")).strip()
            i["sku"] = "".join(sel.re(r'skuid: (\d+)'))

            try:
                i["price"] = self.get_price(i["sku"])
            except ValueError:
                print(item_url)
                raise

            i['title'] = i['title'] or xpath_exchange(sel.xpath('//div[@class="sku-name"]/text()'))
        #self.dbconn.insert(i)
        self.check_if_mine(i)
        return i

    def check_if_mine(self, item):
        if item.get("shopid") in self.settings.get("SHOP_lIST"):
            self.product_file.write("我们的商品%s在第%s个出现\r\n"%(item.get("sku").encode("utf-8"), item.get("order")))

    def extract_zhiying(self, count, item):
        i = dict()
        i["order"] = count
        i["shop"] = "自营"

        try:
            i["price"] = xpath_exchange(item.xpath('.//div[@class="p-price"]/strong/i/text()')) or \
            self.get_price(xpath_exchange(item.xpath("../@data-sku")))
        except ValueError:
            raise

        i["title"] = xpath_exchange(item.xpath('.//div[@class="p-name p-name-type-2"]/a/@title'))
        #self.dbconn.insert(i)
        return i