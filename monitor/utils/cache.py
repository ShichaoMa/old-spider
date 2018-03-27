import time

from redis import Redis
from os.path import getsize
from functools import wraps


class RedisIndex(object):

    def __init__(self, url):
        self.redis_conn = Redis.from_url(url)
        self.hash = dict()

    def exists(self, filename):
        size = self.hash.get(filename)
        if not size:
            size = self.redis_conn.get(filename)
            pipeline = self.redis_conn.pipeline(False)
            if not (size and int(size)):
                try:
                    size = getsize(filename)
                    pipeline.set(filename, size)
                except FileNotFoundError:
                    size = 0
            if size:
                self.hash[filename] = int(size)
            pipeline.hincrby("access_count", filename)
            pipeline.execute()
        return int(size)

    def statistic(self, data, lock):
        data["exsit_cost"] = 0

        @wraps(self.exists)
        def wrapper(*args, **kwargs):
            t1 = time.time()
            result = self.exists(*args, **kwargs)
            lock.acquire()
            data["exsit_cost"] += time.time() - t1
            lock.release()
            return result
        return wrapper
