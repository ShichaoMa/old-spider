# -*- coding:utf-8 -*-
import json
import time
import pickle

from threading import Thread
from abc import abstractmethod, ABCMeta

from toolkit import duplicate, timeout
from toolkit.managers import ExceptContext
from toolkit.monitors import ItemConsumer, ItemProducer

from .task_scheduler import RedisTaskScheduler


class Roller(ItemConsumer, metaclass=ABCMeta):
    name = "Roller"
    task_scheduler = None

    def __init__(self):
        super(Roller, self).__init__()
        self.task_scheduler = RedisTaskScheduler(
            self.settings.get("REDIS_URL"), self.settings.get_int("DELAY", 1000),
            self.name, lambda item: item["item_id"], self.delay_role)
        self.children.append(self.task_scheduler.sender)
        self.children.append(self.task_scheduler.receiver)
        self.task_scheduler.start()

    def retrieve_messages(self):
        while self.alive:
            if not self.consume(callback=self.retrieve_message, errback=self.errback):
                time.sleep(1)

    def errback(self, message):
        for tp in self.consumer.assignment():
            if tp.partition == message.partition:
                self.consumer.seek(tp, message.offset - 1)

    def attach(self, item):
        return item

    def retrieve_message(self, value):
        message = json.loads(value)
        for item in message["items"]:
            if not self.filter(item, message["trace"]):
                continue
            self.task_scheduler.push(pickle.dumps(self.attach(item)))
        return True

    def consume_messages(self, count, filter_key=lambda x: x):
        return duplicate((pickle.loads(message) for message in self.task_scheduler.retrieve(count)), key=filter_key)

    def push_back(self, *messages):
        self.task_scheduler.push(*map(pickle.dumps, messages), delay=False)

    def push(self, *messages):
        self.task_scheduler.push(*map(pickle.dumps, messages))

    def start(self):
        with ExceptContext(errback=lambda *args: self.log_err(*args) and self.stop() is None, finalback=self.close):
            retriever = Thread(target=self.retrieve_messages)
            self.children.append(retriever)
            retriever.setDaemon(True)
            retriever.start()
            self.roll()

    def close(self, got_err):
        super(Roller, self).close()
        self.task_scheduler.input_channel.close()
        self.task_scheduler.output_channel.close()
        self.logger.info("Exit. ")

    def stop(self, *args):
        super(Roller, self).stop(*args)
        if self.task_scheduler:
            self.task_scheduler.alive = False

    @abstractmethod
    def roll(self):
        pass

    @abstractmethod
    def filter(self):
        pass

    @abstractmethod
    def delay_role(self, message, default):
        pass


class ItemEnricher(Roller, ItemProducer, metaclass=ABCMeta):
    """
        Filter base.
    """
    name = "item_filter"
    command = "ENRICH"
    version = "1.0.0"
    failed_items = dict()

    def attach(self, item):
        item["delay_date"] = time.time() * 1000
        return item

    def delay_role(self, message, default):
        return default

    def deal_with_result(self, rs, old):
        if rs.failed():
            self.logger.error("Celery failed: %s, Error: %s" % (old["item_id"], rs.result))
            self.push(old)
        else:
            new = rs.get(propagate=False)
            if new["result"]:
                new["command"] = self.command
                new["version"] = self.version
                new["references"] = []
                new.pop("result")
                new.pop("failed_reason", None)
                self.logger.info("Send %s to %s. " % (old["item_id"], self.topic_out))
                self.task_scheduler.remove(old["item_id"])
                if old["item_id"] in self.failed_items:
                    del self.failed_items[old["item_id"]]
                self.produce(json.dumps(new))
            else:
                failed_times = self.failed_items.setdefault(old["item_id"], 0) + 1
                self.failed_items[old["item_id"]] = failed_times
                if failed_times < self.settings.get_int("FAILED_TIMES", 10):
                    self.push(old)
                    self.logger.error("Error: %s. push %s task back. " % (new.get("failed_reason"), old["item_id"]))
                else:
                    self.logger.error("Error: %s. %s for %s times, abandon. "%(
                        new.get("failed_reason"), old["item_id"], failed_times))

    @timeout(8, True)
    def tear_off(self, result_list):
        while result_list:
            self.look_for_ready(result_list)

    def look_for_ready(self, result_list):
        index = 0
        while index < len(result_list):
            roc_item, result, process_time = result_list[index]
            if not result:
                self.logger.info("Call celery timeout, push task back. ")
                result_list.pop(index)
                self.push(roc_item)
            elif result.ready():
                result_list.pop(index)
                self.deal_with_result(result, roc_item)
            elif time.time() - process_time > self.settings.get("CELERY_TIMEOUT", 200):
                self.logger.info("Celery timeout, push task back. ")
                result_list.pop(index)
                self.push(roc_item)
            else:
                index += 1
        time.sleep(.1)

    def roll(self):
        result_list = list()
        try:
            while self.alive or [thread for thread in self.children if thread.is_alive()]:
                if len(result_list) < self.settings.get_int("CONCURRENCY", 10):
                    roc_items = self.consume_messages(self.settings.get_int("CONSUME_MAX_COUNT", 100),
                        filter_key=lambda x: (x["item_id"], x["item_type"]))
                    for roc_item in roc_items:
                        with ExceptContext(errback=self.log_err):
                            self.logger.info("Process %s. " % roc_item["item_id"])
                            result_list.append((roc_item, self.enrich(roc_item), time.time()))
                self.look_for_ready(result_list)
                time.sleep(1)
        finally:
            if self.tear_off(result_list):
                for roc_item, result, process_time in result_list:
                    self.logger.info("Push back unfinished task: %s. "%roc_item["item_id"])
                    self.push_back(roc_item)

    @abstractmethod
    def enrich(self, roc_item):
        pass
