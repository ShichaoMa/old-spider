#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import time
import copy
import json
import socket
import select
import random
import requests
import traceback

import subprocess
from redis import Redis
from bs4 import BeautifulSoup
from queue import Queue, Empty
from threading import Thread, RLock
from argparse import ArgumentParser
from collections import defaultdict, OrderedDict

from selenium.webdriver.support.ui import WebDriverWait

from toolkit import zip, free_port
from toolkit.manager import Timer, ExceptContext

from utils.core.components import Monitor
from utils.selenium_driver import CustomDriver


class OfferListingMonitor(Monitor):
    name = "offer_listing_monitor"
    capabilities = {"capabilities": {
        "firstMatch": [{}],
        "alwaysMatch": {
            "browserName": "firefox",
            "acceptInsecureCerts": True,
            "moz:firefoxOptions": {
                "prefs": {
                    "network.proxy.type": 0,
                    "dom.ipc.plugins.enabled": False,
                    "dom.ipc.plugins.asyncdrawing.enabled": False,
                    "dom.ipc.plugins.flash.subprocess.crashreporter.enabled": False,
                    "dom.ipc.plugins.forcedirect.enabled": False,
                    "dom.ipc.plugins.nativeCursorSupport": False,
                    "dom.ipc.plugins.reportCrashURL": False,
                    "permissions.default.image": 2,
                    # "javascript.enabled": False,
                    "browser.cache.memory.enable": False,
                    "browser.cache.disk.enable": False,
                    "network.http.use-cache": False,
                    "media.gmp-provider.enabled": False,
                    "media.gmp-gmpopenh264.autoupdate": False,
                    "media.gmp-gmpopenh264.provider.enabled": False,
                    # "network.proxy.http": "mh111.headedeagle.com",
                    # "network.proxy.http_port": 12017,
                    # "network.proxy.ssl": "192.168.200.51",
                    # "network.proxy.ssl_port": 8123
                }
            }
        }
    }
    }
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }
    user_agents = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36
Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36
Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0
Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0
Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0
Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0
Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko
Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)
Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10
Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0
Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50
Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)
Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1
Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1
Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11
Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60
Opera/8.0 (Windows NT 5.1; U; en)
Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50
Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0
Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11
Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36
Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)
Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)""".split("\n")

    def __init__(self, settings, engines):
        super(OfferListingMonitor, self).__init__(settings)
        self.engines = dict(engine.split("*") for engine in engines)
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT"))
        self.proxy_sets = self.settings.get("PROXY_SETS", "proxy_set").split(",")
        self.proxies_in_use = defaultdict(OrderedDict)
        self.set_logger()
        self.lock = RLock()
        self.clients = dict()
        self.workers = []
        self.client_queue = Queue()
        socket.setdefaulttimeout(self.settings.get("OFFER_LISTING_TIMEOUT", 15))
        self.server = socket.socket()
        self.server.bind((self.settings.get("DRIVER_HOST", ""), self.settings.get_int("DRIVER_PORT", 1234)))
        self.logger.info("Listen to %s:%s"%(self.settings.get("DRIVER_HOST", ""), self.settings.get_int("DRIVER_PORT", 1234)))
        self.server.listen(self.settings.get_int("LISTEN", 5))

    def start(self):
        os.makedirs(self.settings.get("LOG_DIR"), exist_ok=True)
        for engine, workers in self.engines.items():
            for i in range(int(workers)):
                worker = Thread(target=getattr(self, "process_%s"%engine), name="%s_%s"%(engine, i), args=(i,
                    os.path.join(self.settings.get("LOG_DIR"), "driver.%s.log"%(i+1)), ))
                self.workers.append(worker)
                self.children.append(worker)
                worker.start()
        try:
            while self.alive or self.clients or [worker for worker in self.workers if worker.is_alive()]:
                readable = list(self.clients.keys())+[self.server] if self.alive else self.clients.keys()
                r = None
                try:
                    readable, writable, _ = select.select(readable, self.clients.keys(), self.clients.keys(), 0.1)
                    for r in readable:
                        if r == self.server:
                            if len(self.clients) < sum(map(
                                    int, self.engines.values())) + self.settings.get_int("WAITING_CLIENTS", 10) and self.alive:
                                client, addr = r.accept()
                                self.logger.debug("Receive client from %s. current_client_length: %s"%(addr, len(self.clients)))
                                self.clients.setdefault(client, dict())["addr"] = addr
                        else:
                            url = r.recv(1024).decode("utf-8")
                            if url:
                                self.logger.debug("Receive url %s from %s:%s. " % ((url,) + self.clients[r]["addr"]))
                                self.clients.setdefault(r, dict())["url"] = url
                                self.clients[r]["start_time"] = time.time()
                                self.client_queue.put(self.clients[r])
                    for w in writable:
                        other = self.clients[w].get("other")
                        if other:
                            try:
                                w.send(other)
                            finally:
                                try:
                                    w.close()
                                finally:
                                    del self.clients[w]
                except Exception as e:
                    self.logger.error("Error in start : %s"%traceback.format_exc())
                    if r in self.clients.keys():
                        try:
                            r.close()
                        except Exception:
                            pass
                        finally:
                            del self.clients[r]
                for index, worker in enumerate(self.workers[:]):
                    if self.alive and not worker.is_alive():
                        engine, i = worker.name.split("_")
                        worker = Thread(
                            target=getattr(self, "process_%s" % engine), name=worker.name, args=(
                                int(i), os.path.join(self.settings.get("LOG_DIR"), "driver.%s.log" % (int(i) + 1)),))
                        self.workers[index] = worker
                        self.children[index] = worker
                        self.logger.info("Restart worker %s. "%i)
                        worker.start()
        finally:
            self.server.close()

    def _get_proxy(self):
        """
         随机选取代理
         :return: 代理
         """
        proxy = self.redis_conn.srandmember(random.choice(self.proxy_sets))
        if proxy:
            proxy = proxy.decode("utf-8")
            if proxy.count(".") == 3:
                proxy = tuple(proxy.split(":"))
            else:
                proxy = proxy.split(":")
                proxy.append(self.settings.get("PROXY_ACCOUNT_PASSWORD"))
            return tuple(proxy)

    def proxies_choice(self, engine, remove=False, proxy=None):
        with self.lock:
            if remove and proxy in self.proxies_in_use[engine]:
                # 删除不可用代理
                self.proxies_in_use[engine].pop(proxy)
            proxy = self._get_proxy()
            try:
                # 获取first代理，比较麻烦，先取出来，然后再放回去，位置不变
                first_proxy, ts = self.proxies_in_use[engine].popitem(last=False)
                self.proxies_in_use[engine][first_proxy] = ts
                self.proxies_in_use[engine].move_to_end(first_proxy, False)
            except KeyError as e:
                print(e)
                first_proxy = None
            while proxy in self.proxies_in_use[engine] and proxy != first_proxy:
                proxy = self._get_proxy()
            self.proxies_in_use[engine][proxy] = time.time()
            self.proxies_in_use[engine].move_to_end(proxy)
            return proxy

    def process_curl(self, index, log_path):
        self.logger.debug("Start in process curl. ")
        proxy = self.proxies_choice("curl")
        while self.alive or self.clients:
            with ExceptContext(Exception, errback=self.log_err):
                try:
                    meta = self.client_queue.get_nowait()
                except Empty:
                    time.sleep(.1)
                    continue
                try:
                    while True:
                        user_agent = random.choice(self.user_agents)
                        cmds = ['curl',
                                '-o',
                                '-',
                                '-s',
                                '-w',
                                '%{http_code}',
                                meta.get("url"),
                                '-H',
                                'Accept: text/html,application/xhtml+xml,'
                                'application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                                '-H',
                                'Connection: keep-alive',
                                '-H',
                                'Accept-Encoding: gzip, deflate, br',
                                '-H',
                                'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
                                '-H',
                                'User-Agent: %s'%user_agent,
                                '--compressed',
                                '--connect-timeout',
                                '10'
                                ]
                        if proxy:
                            cmds.append("-x")
                            cmds.append("http://%s:%s"%(proxy[0], proxy[1]))
                            if len(proxy) == 3:
                                cmds.append("-U")
                                cmds.append(proxy[2])
                        with Timer() as timer:
                            process = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            fs = select.select([process.stdout], [], [], self.settings.get_int("OFFER_LISTING_TIMEOUT", 10))
                            if process.stdout in fs[0]:
                                bodylines = process.stdout.readlines()
                                status = int(bodylines[-1].strip())
                            else:
                                self.logger.error("Worker %s, url: %s: Unknow error"%(index, meta.get("url")))
                                status = 999
                            try:
                                os.kill(process.pid, 9)
                                process.wait()
                            except Exception as e:
                                print(e)
                                pass
                        if status == 200:
                            self.logger.debug(
                                "Worker %s use requests got html. total cost: %s, request cost: %s, url: %s, proxy: %s" % (
                                    index, timer.stop - meta["start_time"], timer.cost, meta.get("url"), proxy))
                            body = b"".join(bodylines[:-2]).decode()
                            soup = BeautifulSoup(body, "html")
                            with Timer() as timer:
                                prices = [price.get_text() for price in
                                          soup.find_all("span", attrs={"class": "a-size-large a-color-price olpOfferPrice a-text-bold"}) +
                                          soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row  .a-size-large')]
                                shipping_costs = [shipping_cost.get_text() for shipping_cost in
                                                  soup.select('p[class="olpShippingInfo"]') +
                                                  soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row p[class="olpShippingInfo"]')]
                                merchurts = [merchurt.get_text() for merchurt in soup.select('h3[class="a-spacing-none olpSellerName"] a')]
                                buffer = json.dumps(list(zip(prices, shipping_costs, merchurts)))
                            self.logger.debug("Worker %s: url: %s, parse cost: %s offer listing data: %s" % (
                                index, meta.get("url"), timer.cost, buffer))
                            if buffer == "[]" or prices and prices[0] and prices[0].strip():
                                meta["other"] = buffer.encode("utf-8")
                            else:
                                meta["other"] = b"error"
                        elif status == 503:
                            self.logger.error("In cur: 503 status code returned. ")
                            meta["other"] = b"error"
                            proxy = self.proxies_choice("curl")
                            self.logger.info("Worker %s change proxy to %s. " % (index, proxy))
                        else:
                            self.logger.error("Curl return unknown error: %s"%status)
                            proxy = self.proxies_choice("curl", remove=True, proxy=proxy)
                            self.logger.info("Worker %s change proxy to %s. " % (index, proxy))
                            continue
                        break
                except Exception:
                    self.logger.error("Error in get: %s" % traceback.format_exc())
                    meta["other"] = b"error"

    def connect_client(self):
        self.lock.acquire()
        try:
            process = None
            client = None
            while True:
                try:
                    port = free_port()
                    process = subprocess.Popen(["./requests_client.py", "--port", str(port)])
                    client = socket.socket()
                    time.sleep(1)
                    client.connect(("", port))
                    return process, client
                except Exception as e:
                    print(e)
                    try:
                        client and client.close()
                    except:
                        pass
                    process and process.poll() is None and not process.terminate() and process.wait()
        finally:
            self.lock.release()

    def process_requests(self, index, log_path):
        session = requests.Session()
        self.logger.debug("Start in process requests. ")
        proxy = self.proxies_choice("requests")
        while self.alive or self.clients:
            with ExceptContext(Exception, errback=self.log_err):
                try:
                    meta = self.client_queue.get_nowait()
                except Empty:
                    time.sleep(.1)
                    continue
                try:
                    while True:
                        user_agent = random.choice(self.user_agents)
                        headers = self.headers.copy()
                        headers["User-Agent"] = user_agent.strip()
                        if proxy:
                            if len(proxy) == 2:
                                proxies = {"https": "http://%s:%s" % proxy}
                            else:
                                proxies = {"https": "http://%s@%s:%s" % (proxy[2], proxy[0], proxy[1])}
                        else:
                            proxies = None
                        with Timer() as timer:
                            try:
                                self.logger.debug("Worker %s: url: %s start request. "%(index, meta.get("url")))
                                resp = session.get(meta["url"], headers=headers, proxies=proxies,
                                                   timeout=self.settings.get_int("OFFER_LISTING_TIMEOUT", 10), stream=True)
                                body = b""
                                for chunk in resp.iter_content(10240):
                                    body += chunk
                                status_code = resp.status_code
                            except Exception:
                                self.logger.error("Error: %s" % traceback.format_exc())
                                status_code = 888
                        if status_code == 200:
                            self.logger.info(
                                "Worker %s use requests got html. total cost: %s, request cost: %s, url: %s, proxy: %s"%(
                                    index, timer.stop - meta["start_time"], timer.cost, meta.get("url"), proxy))
                            with Timer() as timer:
                                soup = BeautifulSoup(body.decode(), "html")
                                prices = [price.get_text() for price in
                                          soup.find_all("span", attrs={"class": "a-size-large a-color-price olpOfferPrice a-text-bold"}) +
                                          soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row  .a-size-large')]
                                shipping_costs = [shipping_cost.get_text() for shipping_cost in
                                                  soup.select('p[class="olpShippingInfo"]') +
                                                  soup.select('.a-container.olpMobileOffer.olpNoPadding > .a-row p[class="olpShippingInfo"]')]
                                merchurts = [merchurt.get_text() for merchurt in soup.select('h3[class="a-spacing-none olpSellerName"] a')]
                                buffer = json.dumps(list(zip(prices, shipping_costs, merchurts)))
                            self.logger.debug("Worker %s: url: %s, parse cost: %s offer listing data: %s" % (
                                index, meta.get("url"), timer.cost, buffer))
                            if buffer == "[]" or prices and prices[0] and prices[0].strip():
                                meta["other"] = buffer.encode("utf-8")
                            else:
                                meta["other"] = b"error"
                        else:
                            self.logger.error("In requests: error code: %s"%status_code)
                            proxy = self.proxies_choice("requests", remove=status_code!=503, proxy=proxy)
                            self.logger.info("Worker %s change proxy to %s. " % (index, proxy))
                            continue
                        break
                except Exception:
                    self.logger.error("Error in get: %s" % traceback.format_exc())
                    meta["other"] = b"error"
        session.close()

    def init_driver(self, log_path, driver=None):
        if driver:
            driver.quit()
        proxy = self.proxies_choice("selenium")
        self.logger.info("Change proxy to %s. "%str(proxy))
        capabilities = copy.deepcopy(self.capabilities)
        if proxy:
            capabilities["capabilities"]["alwaysMatch"]["moz:firefoxOptions"]["prefs"]["network.proxy.ssl"] = proxy[
                0]
            capabilities["capabilities"]["alwaysMatch"]["moz:firefoxOptions"]["prefs"]["network.proxy.ssl_port"] = \
            proxy[1]
            capabilities["capabilities"]["alwaysMatch"]["moz:firefoxOptions"]["prefs"]["network.proxy.type"] = 1
        return CustomDriver("geckodriver", log_path, capabilities, proxy)

    def process_selenium(self, index, log_path):
        self.logger.debug("Start driver, log to %s. "%log_path)
        driver = self.init_driver(log_path)

        while self.alive or self.clients:
            with ExceptContext(Exception, errback=self.log_err):
                try:
                    meta = self.client_queue.get_nowait()
                except Empty:
                    time.sleep(1)
                    continue
                other = self.process(meta["url"], driver).encode("utf-8")
                meta["other"] = other
                if other == b"error":
                    time.sleep(60)
                    driver = self.init_driver(log_path, driver)
        driver.quit()

    def map(self, l, key=lambda x: x.text):
        try:
            return list(map(key, l))
        except Exception as e:
            print(e)
            return []

    def process(self, url, driver, proxy=None):
        self.logger.debug("Process %s ." % url)
        with ExceptContext(Exception, errback=self.log_err):
            driver.get(url)
            WebDriverWait(driver, 10).until(
                lambda driver: driver.find_element_by_xpath('//div[@class="a-section a-padding-small"]|//body/center/p/table|//div[@id="g"]'))
            try:
                ele = driver.find_element_by_xpath('//div[@class="a-section a-padding-small"]')
            except Exception:
                ele = None
            if ele:
                self.logger.debug("In selenium: Got html. url: %s, proxy: %s"%(url, str(proxy)))
                prices = driver.find_elements_by_xpath('//span[@class="a-size-large a-color-price olpOfferPrice a-text-bold"]')
                shipping_costs = driver.find_elements_by_xpath('//p[@class="olpShippingInfo"]//b')
                merchurts = driver.find_elements_by_xpath('//h3[@class="a-spacing-none olpSellerName"]//a')
                buffer = json.dumps(list(zip(self.map(prices), self.map(shipping_costs), self.map(merchurts))))
                self.logger.debug("Offer listing data: %s"%buffer)
                if prices and prices[0] and prices[0].text.strip():
                    return buffer
                else:
                    return "error"
            else:
                self.logger.error("In selenium: 503 status code returned. ")
                return "error"
        return "error"

    @classmethod
    def parse_args(cls):
        parser = ArgumentParser(conflict_handler="resolve")
        parser.add_argument("-s", "--settings", help="Settings. ", default="settings.py")
        parser.add_argument("engines", nargs="+", help="use curl, selenium or requests to send request. eg: curl*3 means use 3 workers of curl to send request. ")
        args = parser.parse_args()
        return cls(args.settings, args.engines)


if __name__ == "__main__":
    OfferListingMonitor.parse_args().start()