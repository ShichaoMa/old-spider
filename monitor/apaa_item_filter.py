#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import json
import time
import requests
import traceback

from redis import Redis
from scrapy import Selector
from threading import Thread, RLock

from utils.aws_signed_request import aws_signed_request
from utils.core import ItemFilter


class APAAItemFilter(ItemFilter):
    """
        使用amazon webservice api进行ean mpn upc等信息获取
    """
    name = "apaa_item_filter"

    def __init__(self, **kwargs):
        super(APAAItemFilter, self).__init__(**kwargs)
        self.redis_conn = Redis(self.settings.get("REDIS_HOST", "REDIS_POST"))
        self.apaa_queue = "apaa_queue"
        self.flush_time = time.time()
        self.lock = RLock()

    def start(self):
        for apaa_thread in range(self.settings.get("APAA_THREADS", 3)):
            thread = Thread(target=self.process_apaa)
            self.children.append(thread)
            thread.start()
        super(APAAItemFilter, self).start()

    def process_message(self, message):
        """
        处理kafka消息统一接口，子类分别实现
        将需要进行apaa请求的消息放入一个redis队列中
        :param message:
        :return:
        """
        # try:
        #     item = json.loads(message)
        #     if item.get("collection_name") == "jay_amazons" and item.get("parent_asin"):
        #         self.redis_conn.lpush(self.apaa_queue, message)
        #     else:
        #         self.logger.info(
        #             "Send update or other site message to kafka topic: %s directly, crawlid: "
        #             "%s, product_id: %s, spiderid: %s. "%(
        #                 self.topic_out, item.get("crawlid"), item.get("product_id"), item.get("spiderid")))
        #         return message
        # except Exception:
        #     self.logger.error("Error in process_message: %s. "%traceback.format_exc())
        return message

    def process_apaa(self):
        """
        发送apaa请求子线程，队列中的消息数大于10时，统一发送一次webservice请求
        """
        while self.alive:
            items = []
            self.lock.acquire()
            if self.redis_conn.llen(self.apaa_queue) > 10 or \
                                    self.flush_time + self.settings.get("API_TIMEWAITING", 30) < time.time():
                for i in range(10):
                    message = self.redis_conn.rpop(self.apaa_queue)
                    if message:
                        item = json.loads(message)
                        items.append(item)
                    else:
                        break
            self.lock.release()
            if items:
                try:
                    self.flush_time = time.time()
                    parent_asins = [i.get("parent_asin") for i in items]
                    self.logger.debug("Apaa request: %d, %s. " % (len(parent_asins), parent_asins))
                    url = aws_signed_request('com', {
                        'Operation': 'ItemLookup',
                        'ItemId': ','.join(parent_asins),
                        'ResponseGroup': 'ItemAttributes'})
                    resp = requests.get(url, timeout=10)
                    self.logger.info("Apaa response code: %s. " % resp.status_code)
                    partial_items = dict((x.get("parent_asin"), x) for x in items)

                    for code in ["upc", "ean", "mpn"]:
                        lst = Selector(text=resp.text).xpath(
                            '//%s/text()|//%s/../../asin/text()' % (code, code)).extract()
                        for i in range(0, len(lst), 2):
                            item = partial_items.get(lst[i])
                            item[code] = lst[i + 1]
                    for item in items:
                        self.logger.info(
                            "Send appa message to kafka topic: %s successfully, crawlid: "
                            "%s, product_id: %s, spiderid: %s. " % (
                                self.topic_out, item.get("crawlid"), item.get("product_id"), item.get("spiderid")))
                except Exception:
                    self.logger.error("Error in process_apaa: %s. "%traceback.format_exc())
                finally:
                    self.produce([json.dumps(item) for item in items])
            else:
                time.sleep(1)


if __name__ == "__main__":
    APAAItemFilter.parse_args().start()