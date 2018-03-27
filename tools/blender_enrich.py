import time
from redis import Redis
from functools import wraps


class BulkFunc(object):
    """
    用来装饰批量执行函数, eg:
    @BulkFunc
    def callback(item_list, **kwargs):
        ....
    callback提供一个参数item_list
    为每批次的item
    """
    def __init__(self, size):
        """
        :param size: batch大小
        """
        self.size = size
        self.item_list = list()

    def __call__(self, func):
        @wraps(func)
        def wrapper(item=None, self=self, immediately=False):
            if item:
                self.item_list.append(item)
            if len(self.item_list) >= self.size or immediately:
                func(self.item_list)
                self.item_list.clear()
        return wrapper


def bulk(iterable, callback):
    """
    批量执行函数
    :param iterable: 可迭代对象
    :param callback: BulkFunc对象
    :return:
    """
    for item in iterable:
        callback(item)
    callback(immediately=True)


def main():
    redis_conn = Redis.from_url("redis://192.168.200.150:6379/11")

    @BulkFunc(1000)
    def callback(item_list, redis_conn=redis_conn):
        pipeline = redis_conn.pipeline(False)
        pipeline.multi()
        for item in item_list:
            pipeline.zrank("blender_set", item)
        for index, rs in enumerate(pipeline.execute()):
            if not rs:
                redis_conn.zadd("blender_set", item_list[index], time.time() + 1000000)
                #print("Add %s to blender_set"%item_list[index])

    bulk(redis_conn.hkeys("blender_hash"), callback)


if __name__ == "__main__":
    main()