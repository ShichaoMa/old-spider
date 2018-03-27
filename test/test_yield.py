# -*- coding:utf-8 -*-
import time
import threading
import asyncio


def fun():
    yield time.sleep(3)

@asyncio.coroutine
def hello(index):                   # 通过装饰器asyncio.coroutine定义协程
    print('Hello world! index=%s, thread=%s' % (index, threading.currentThread()))
    yield from asyncio.sleep(2)    # 模拟IO任务
    print('Hello again! index=%s, thread=%s' % (index, threading.currentThread()))

loop = asyncio.get_event_loop()     # 得到一个事件循环模型
tasks = [hello(1), hello(2)]        # 初始化任务列表
loop.run_until_complete(asyncio.wait(tasks))    # 执行任务
loop.close()