#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import json
import time
import pickle
import datetime
import requests
import traceback

from threading import Thread
from argparse import ArgumentParser
from toolkit import groupby, duplicate
from toolkit.manager import ExceptContext, Blocker

from utils.core import ItemConsumer

from utils.task_scheduler import RedisTaskScheduler


class Blender(ItemConsumer):

    name = "blender"
    do = {
        "ETBY": lambda x: datetime.datetime.now().weekday() != 4
    }

    def __init__(self, **kwargs):
        super(Blender, self).__init__(**kwargs)
        self.task_scheduler = RedisTaskScheduler(self.settings.get("REDIS_URL"), self.settings.get_int("DELAY"),
                                                "blender", lambda message: message["data"]["roc_id"],
                                                path=self.settings.get("CHANNEL_PATH", "."))
        self.children.append(self.task_scheduler.sender)
        self.children.append(self.task_scheduler.receiver)
        print("Heath or not: %s" % self.task_scheduler.is_health(), flush=True)
        self.task_scheduler.start()
        self.jay_api = "http://%s:%s/api/update" % (
            self.settings.get("HOST"), self.settings.get_int("PORT"))

    def retrieve_messages(self):
        while self.alive:
            if not self.consume(callback=self._retrieve_message, errorback=self.errorback):
                time.sleep(1)

    def errorback(self, message):
        for tp in self.consumer.assignment():
            if tp.partition == message.partition:
                self.consumer.seek(tp, message.offset-1)

    def _retrieve_message(self, value):
        message = json.loads(value)
        if message["event"] == "updated" or \
                        message["source_site_code"] in self.settings.get("IGNORE_SITE", "CSMPUS").split(","):
            return True
        try:
            self.task_scheduler.push(pickle.dumps(message))
        except Exception as e:
            print(e)
            return False
        return True

    def consume_messages(self, count):
        return duplicate(
            (pickle.loads(message) for message in self.task_scheduler.retrieve(count)),
            key=lambda x: x["data"]["roc_id"])

    def close(self, got_err):
        self.task_scheduler.input_channel.close()
        self.task_scheduler.output_channel.close()
        self.logger.info("Exit in start. ")

    def start(self):
        with ExceptContext(errback=lambda *args: self.log_err(*args) and self.stop() is None, finalback=self.close):
            retriever = Thread(target=self.retrieve_messages)
            self.children.append(retriever)
            retriever.start()
            while self.alive or [thread for thread in self.children if thread.is_alive()]:
                with Blocker(self.settings.get_int("INTERVAL", 10 * 60), self, notify=lambda instance: not instance.alive) as blocker:
                    if blocker.is_notified:
                        continue
                    print("Heath or not: %s" % self.task_scheduler.is_health(), blocker.is_notified, [thread for thread in self.children if thread.is_alive()], flush=True)
                    need_crawl_messages = self.consume_messages(self.settings.get_int("CONSUME_MAX_COUNT", 100000))
                    if need_crawl_messages and self.alive:
                        self.logger.debug("Got %s messages to build crawl task. "%len(need_crawl_messages))
                        for site, messages in groupby(
                                need_crawl_messages, lambda message: message["source_site_code"]).items():
                            if not site:
                                continue
                            if self.can_do(site):
                                # 发送jay-monitor,每一千条分开发送
                                while messages and self.alive:
                                    count = 0
                                    sub_messages = []
                                    while messages and count < self.settings.get_int("TERM_COUNT", 5000):
                                        sub_messages.append(messages.pop())
                                        count += 1
                                    self.send(site, sub_messages)
                                    time.sleep(1)
                            # 当且仅当self.alive = False时，messages才不会空，这时，为了防止信息丢失，我们重新将message放回output_channel,下同
                            if messages:
                                #print("deep 2 len: %s" % len(messages))
                                self.task_scheduler.push(*map(
                                    lambda message: pickle.dumps(message), messages), delay=False)
                    else:
                        #print("deep 1 len: %s" % len(need_crawl_messages))
                        if need_crawl_messages:
                            self.task_scheduler.push(*map(
                                lambda message: pickle.dumps(message), need_crawl_messages), delay=False)
                        self.logger.debug("Haven't got expired message. ")
                print("Heath or not: %s" % self.task_scheduler.is_health(), flush=True)

    def send(self, site, messages):
        send_failed = False
        try:
            resp = requests.post(self.jay_api, json={"site": site.lower(), "messages": messages})
            self.logger.info("Jay api returns %s. "%resp.status_code)
            if resp.status_code == 200:
                self.logger.info("Update %s items of %s. " % (len(messages), site))
            else:
                self.logger.error("Update %s interrupt, code: %s, error: %s. " % (
                    site, resp.status_code, resp.text))
                send_failed = True
            return resp
        except Exception:
            self.logger.error("Error in send: %s"%traceback.format_exc())
            send_failed = True
        finally:
            #print("deep 3 len: %s" % len(messages))
            if send_failed:
                self.task_scheduler.push(*map(
                    lambda message: pickle.dumps(message), messages), delay=False)
            else:
                self.task_scheduler.push(*map(
                    lambda message: pickle.dumps(message), messages))
            self.logger.info("Redelay %s messages %s. "%(
                len(messages), "immediately" if send_failed else "to next cycle"))

    def can_do(self, site):
        return self.do.get(site, lambda x: True)(None)

    def stop(self, *args):
        self.task_scheduler.alive = False
        self.alive = False
        with ExceptContext(errback=lambda *args: True):
            if self.consumer:
                self.consumer.close()

    @classmethod
    def run(cls):
        parser = ArgumentParser()
        cls.enrich_parser_arguments(parser)
        bd = cls(**vars(parser.parse_args()))
        bd.start()


if __name__ == "__main__":
    Blender.run()
