#!/usr/bin/env python3.6
import os
import bs4
import time
import json
import random
import asyncio
import aiohttp
import traceback

from redis import Redis
from threading import Thread
from os.path import dirname, join
from collections import OrderedDict

from toolkit.managers import Timer
from toolkit.monitors import Service, LoggingMonitor


class Worker(LoggingMonitor):
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': "close",
    }
    user_agents = open(join(dirname(__file__), "user_agents.list"), "r").read().split("\n")

    def __init__(self, monitor, indent, proxy):
        super(Worker, self).__init__(monitor.settings)
        self.indent = indent
        self.proxy = proxy
        self.proxy_auth = aiohttp.BasicAuth(*self.settings.get("PROXY_ACCOUNT_PASSWORD").split(":"))
        self.monitor = monitor
        self.step = 0
        self.start_time = time.time()
        self.running = False

    async def process(self, reader):
        self.running = True
        self.start_time = time.time()
        with Timer() as timer:
            url = (await reader.read(1024)).decode()
            self.step = 1
            while True:
                user_agent = random.choice(self.user_agents)
                headers = self.headers.copy()
                headers["User-Agent"] = user_agent.strip()
                self.logger.debug("Worker: %s url: %s start request. proxy:%s" % (
                    self.indent, url, self.proxy))
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, verify_ssl=False,
                                                    headers=headers,
                                                    proxy=self.proxy,
                                                    proxy_auth=self.proxy_auth) as resp:
                            self.logger.debug(
                                "Worker: %s url: %s receive response. proxy: %s" % (self.indent, url, self.proxy))
                            self.step = 2
                            body = await resp.read()
                            status_code = resp.status
                except Exception:
                    self.logger.error("Error: %s" % traceback.format_exc())
                    status_code = 888
                self.step = 3
                if status_code == 200:
                    self.logger.info("Worker: %s Got html. url: %s, proxy: %s" % (
                        self.indent, url, self.proxy))
                    soup = bs4.BeautifulSoup(body.decode(), "html")
                    prices = [price.get_text() for price in
                              soup.find_all("span", attrs={
                                  "class": "a-size-large a-color-price olpOfferPrice a-text-bold"}) +
                              soup.select(
                                  '.a-container.olpMobileOffer.olpNoPadding > .a-row  .a-size-large')]
                    shipping_costs = [shipping_cost.get_text() for shipping_cost in
                                      soup.select('p[class="olpShippingInfo"]') +
                                      soup.select(
                                          '.a-container.olpMobileOffer.olpNoPadding > '
                                          '.a-row p[class="olpShippingInfo"]')]
                    merchurts = [merchurt.get_text() for merchurt in
                                 soup.select('h3[class="a-spacing-none olpSellerName"] a')]
                    buffer = json.dumps(list(zip(prices, shipping_costs, merchurts)))
                    self.logger.debug("Worker: %s offer listing data: %s" % (self.indent, buffer))
                    if not (buffer == "[]" or prices and prices[0] and prices[0].strip()):
                        buffer = "error"
                    break
                else:
                    self.logger.error("Worker: %s in requests: error code: %s" % (self.indent, status_code))
                    self.proxy = self.monitor.proxies_choice(remove=status_code != 503, proxy=self.proxy)
                    self.logger.info("Worker: %s change proxy to %s. " % (self.indent, self.proxy))
        self.logger.debug("Task cost : %s. "%timer.cost)
        self.step = 0
        self.running = False
        return buffer.encode()

    def __str__(self):
        return "<Worker indent=%s proxy=%s step=%s>" % (self.indent, self.proxy, self.step)

    __repr__ = __str__


class OfferListingMonitor(Service):
    name = "offer_listing_monitor"

    def __init__(self):
        super(OfferListingMonitor, self).__init__()
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT"))
        self.proxy_sets = self.settings.get("PROXY_SETS", "proxy_set").split(",")
        self.proxies_in_use = OrderedDict()
        self.workers = [Worker(self, index+1, self.proxies_choice())
                        for index in range(self.settings.get_int("WORKERS", 10))]
        self.server = None

    def start(self):
        check_thread = Thread(target=self.check)
        check_thread.setDaemon(True)
        check_thread.start()
        loop = asyncio.get_event_loop()
        server_coro = asyncio.start_server(self.recv_client, self.settings.get("HOST", ""),
                                           self.settings.get_int("PORT", 1234), loop=loop)
        self.server = loop.run_until_complete(server_coro)
        self.logger.info("Listen to %s:%s" % (self.settings.get("HOST", ""), self.settings.get_int("PORT", 1234)))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        padding = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*padding, self.close()))
        loop.close()

    def check(self):
        while self.alive:
            if [worker for worker in self.workers
                    if time.time() - worker.start_time > self.settings.get("BLOCK_INTERVAL", 600) and worker.running]:
                self.alive = False
                time.sleep(5)
                os.kill(os.getpid(), 9)
            time.sleep(1)

    async def close(self):
        self.server.close()
        await self.server.wait_closed()

    def stop(self, *args):
        self.alive = False
        raise KeyboardInterrupt

    async def recv_client(self, reader, writer):
        is_finish = False
        while self.alive:
            for worker in self.workers:
                if not worker.running:
                    buffer = await worker.process(reader)
                    writer.write(buffer)
                    writer.close()
                    is_finish = True
                    break
            if is_finish:
                break
            await asyncio.sleep(1)

    def _get_proxy(self):
        """
         随机选取代理
         :return: 代理
         """
        proxy = self.redis_conn.srandmember(random.choice(self.proxy_sets))
        if proxy:
            return "http://" + proxy.decode("utf-8")
        return None

    def proxies_choice(self, remove=False, proxy=None):
        if remove and proxy in self.proxies_in_use:
            # 删除不可用代理
            self.proxies_in_use.pop(proxy)
        proxy = self._get_proxy()
        try:
            # 获取first代理，比较麻烦，先取出来，然后再放回去，位置不变
            first_proxy, ts = self.proxies_in_use.popitem(last=False)
            self.proxies_in_use[first_proxy] = ts
            self.proxies_in_use.move_to_end(first_proxy, False)
        except KeyError as e:
            print(e)
            first_proxy = None
        while proxy in self.proxies_in_use and proxy != first_proxy:
            proxy = self._get_proxy()
        self.proxies_in_use[proxy] = time.time()
        self.proxies_in_use.move_to_end(proxy)
        return proxy


if __name__ == "__main__":
    OfferListingMonitor().start()
