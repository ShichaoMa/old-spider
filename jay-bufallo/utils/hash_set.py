import time

from threading import RLock
from toolkit import thread_safe_for_method


class RedisHashSet(object):
    """
    使用hash和zset管理数据
    """
    def __init__(self, redis_conn, key):
        self.redis_conn = redis_conn
        self.hash_key = "%s_hash"%key
        self.set_key = "%s_set"%key
        self.lock = RLock()

    @thread_safe_for_method
    def push(self, message, id, delay):
        self.redis_conn.zadd(self.set_key, id, delay)
        self.redis_conn.hset(self.hash_key, id, message)

    @thread_safe_for_method
    def rid_all(self):
        pipe = self.redis_conn.pipeline()
        pipe.watch(self.set_key)
        pipe.multi()
        pipe.zrangebyscore(self.set_key, 0, time.time() * 1000).zremrangebyscore(
            self.set_key, 0, time.time() * 1000)
        result, count = pipe.execute()
        return result and [message for message in self.redis_conn.hmget(self.hash_key, result) if message]

    def hash_len(self):
        return self.redis_conn.hlen(self.hash_key)

    def set_len(self):
        return self.redis_conn.zcard(self.set_key)

    def __delitem__(self, key):
        self.redis_conn.hdel(self.hash_key, key)
        self.redis_conn.zrem(self.set_key, key)
