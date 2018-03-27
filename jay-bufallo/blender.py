#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import json
import time
import datetime
import requests

from toolkit import groupby, load_class, cache_for
from toolkit.managers import ExceptContext, Blocker


class Blender(load_class("utils.components.Roller")):

    name = "blender"
    do = {
        "ETBY": lambda: datetime.datetime.now().weekday() != 4
    }

    def __init__(self):
        super(Blender, self).__init__()
        self.jay_api = self.settings.get("JAY_API")

    def filter(self, item, trace):
        return item["item_type"] == "Spu" and trace["app"] == "jay"

    @cache_for(60*10)
    def delays(self):
        d = dict()
        with ExceptContext(errback=self.log_err):
            d = dict((line["code"], (line.get("update_interval") or 0) * 1000) for line in json.loads(
                requests.get(self.settings.get(
                    "SOURCE_SITE_API", "http://192.168.200.41:8888/rocapi/v1/source_sites?per_page=20&page=1")).text))
        return d

    def delay_role(self, message, default):
        return self.delays.get(message["item_id"].split("#")[0]) or default

    def can_do(self, site):
        return self.do.get(site, lambda: True)()

    def roll(self):
        while self.alive or [thread for thread in self.children if thread.is_alive()]:
            with Blocker(self.settings.get_int("INTERVAL", 10 * 60), self,
                         notify=lambda instance: not instance.alive) as blocker:
                if blocker.is_notified:
                    return
                with ExceptContext(errback=self.log_err):
                    need_crawl_messages = self.consume_messages(
                        self.settings.get_int("CONSUME_MAX_COUNT", 100000), filter_key=lambda x: x["item_id"])
                    if need_crawl_messages and self.alive:
                        self.logger.info("Got %s messages to build crawl task. " % len(need_crawl_messages))
                        for site, messages in groupby(
                                need_crawl_messages, lambda message: message["meta"]["source_site_code"]).items():
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
                                self.push_back(*messages)
                    else:
                        if need_crawl_messages:
                            self.push_back(*need_crawl_messages)
                        self.logger.info("Haven't got expired message. ")

    def send(self, site, messages):
        send_failed = False
        with ExceptContext(errback=self.log_err) as ec:
            resp = requests.post(self.jay_api, json={"site": site, "messages": messages})
            self.logger.info("Jay api returns %s. " % resp.status_code)
            if resp.status_code == 200:
                self.logger.info("Update %s items of %s. " % (len(messages), site))
            else:
                self.logger.error("Update %s interrupt, code: %s, error: %s. " % (
                    site, resp.status_code, resp.text))
                send_failed = True
        send_failed = send_failed or ec.got_err

        if send_failed:
            self.push_back(*messages)
        else:
            self.push(*messages)
        self.logger.info("Redelay %s messages %s. " % (len(messages), "immediately" if send_failed else "to next cycle"))


if __name__ == "__main__":
    Blender().start()
