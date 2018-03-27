import time
import pickle

from redis import Redis
from threading import Thread
from datetime import datetime

from toolkit.managers import ExceptContext
from toolkit.queues import RedisQueue

from .hash_set import RedisHashSet


class RedisTaskScheduler(object):

    alive = True

    def __init__(self, redis_url, default_delay, task_name, identity, delay_role=lambda message, default: default):
        self.identity = identity
        self.redis_conn = Redis.from_url(redis_url)
        self.input_channel = RedisQueue(self.redis_conn, "%s:input" % task_name)
        self.output_channel = RedisQueue(self.redis_conn, "%s:output" % task_name)
        self.hash_set = RedisHashSet(self.redis_conn, task_name)
        self.default_delay = default_delay
        self.delay_rule = delay_role
        self.sender = Thread(target=self.send)
        self.receiver = Thread(target=self.receive)

    def start(self):
        self.sender.start()
        self.receiver.start()

    def is_health(self):
        difference = self.hash_set.hash_len() - \
                     (len(self.input_channel) + len(self.output_channel) + self.hash_set.set_len())
        return not bool(difference) or difference

    def push(self, *strings, delay=True):
        if delay:
            self.input_channel.push(*strings)
        else:
            self.output_channel.push(*strings)

    def remove(self, item_id):
        del self.hash_set[item_id]

    def pop(self):
        return self.output_channel.pop()

    def retrieve(self, count):
        return self.output_channel.rid(count)

    def send(self):
        while self.alive:
            data = self.input_channel.pop()
            if not data:
                time.sleep(1)
                continue
            if not self.alive:
                self.push(data)
                continue
            message = pickle.loads(data)
            if message.get("event") == "delete":
                del self.hash_set[self.identity(message)]
                continue
            delay_date = message.get("delay_date")
            if delay_date:
                del message["delay_date"]
                expect = delay_date.timestamp()*1000 if isinstance(delay_date, datetime) else delay_date
            else:
                delay = self.delay_rule(message, self.default_delay)
                expect = time.time()*1000 + delay
            with ExceptContext(errback=lambda *args: self.push(data) is None):
                self.hash_set.push(pickle.dumps(message), self.identity(message), expect)

    def receive(self):
        while self.alive:
            with ExceptContext():
                messages = self.hash_set.rid_all()
                # 当messages数量很大时，如果不对messages进行切分导入output_channel，
                # 则push函数调用会持续很久，由于output_channel线程安全，其它线程因此会等待。
                for start in range(0, len(messages), 1000):
                    self.output_channel.push(*messages[start: start+1000])
                    time.sleep(0.01)
            time.sleep(1)
