#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import json
import time

from redis import Redis
from threading import Thread

from toolkit.managers import ExceptContext
from toolkit.translate import Translate
from toolkit import load_function as load_class


class TranslateItemFilter(load_class("components.ItemFilter")):
    """
    对描述信息进行翻译
    """
    name = "translate_item_filter"

    def __init__(self):
        super(TranslateItemFilter, self).__init__()
        self.translate_queue = "translate_queue"
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT", 6379))
        self.description_names = self.settings.get("DESCRIPTION_NAMES").split(",")

    def start(self):
        for translate_thread in range(self.settings.get_int("TRANSLATE_THREADS", 10)):
            thread = Thread(target=self.process_translate)
            self.children.append(thread)
            thread.start()
        super(TranslateItemFilter, self).start()

    def process_message(self, message):
        with ExceptContext(Exception, errback=self.log_err):
            item = json.loads(message)
            if item.get("seed") or item.get("meta").get("type") == "explore":
                crawlid = item.get("crawlid", "")
                if crawlid.isdigit() and len(crawlid) <= 5:
                    self.logger.info("Ignore loco messages: %s" % crawlid)
                    return message
                else:
                    self.redis_conn.lpush(self.translate_queue, message)
            else:
                self.logger.info(
                    "Send update message without translate to kafka topic: %s successfully, crawlid: "
                    "%s, product_id: %s, spiderid: %s. "%(
                        self.topic_out, item.get("crawlid"), item.get("product_id"), item.get("spiderid")))
                return message

    def process_translate(self):
        translator = Translate(self.settings)
        translator.set_logger(self.logger)
        while self.alive:
            message = self.redis_conn.rpop(self.translate_queue)
            if message:
                item = json.loads(message)
                with ExceptContext(Exception, errback=self.log_err):
                    self.logger.info("Explore item processed translate, crawlid: %s, product_id: %s, spiderid: %s. " % (
                        item.get("crawlid"), item.get("product_id"), item.get("spiderid")))

                    descriptions = [(x, item.get(x)) for x in self.description_names if x in item]
                    if descriptions:
                        # 将所有可能的描述字段，使用div包裹起来，统一进行翻译，随后translator会进行按标签分词
                        result = translator.translate("<fdsff>".join(map(lambda x: x[1], descriptions)))
                        for index, cn in enumerate(result.split("<fdsff>")):
                            item["%s_cn"%descriptions[index][0]] = cn
                    self.logger.info(
                        "Send translate message to kafka topic: %s successfully, crawlid: "
                        "%s, product_id: %s, spiderid: %s. " % (
                            self.topic_out, item.get("crawlid"), item.get("product_id"), item.get("spiderid")))
                self.produce(json.dumps(item))
            else:
                time.sleep(1)

    # def consume(self, messages=["name", "word", "text", "name", "word", "text", "name", "word", "text", "name", "word", "text", ]):
    #     """
    #     测试专用
    #     :param messages:
    #     :return:
    #     """
    #     return json.dumps({"product_description": messages.pop(0), "feature": messages.pop(0), "seed": True}) if messages else None
    #
    #
    # def produce(self, message):
    #     """
    #     测试专用
    #     :param message:
    #     :return:
    #     """
    #
    #     print(json.loads(message))
    #     exit(1)


if __name__ == "__main__":
    TranslateItemFilter().start()