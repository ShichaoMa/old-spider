# -*- coding:utf-8 -*-
from multiprocessing import Process, Queue
from queue import Empty
import os
import time
import signal

from multi_thread_closing import MultiThreadClosing


class A(MultiThreadClosing):

    def __init__(self):
        super(A, self).__init__()
        self.set_logger()
        self.pid = os.getpid()
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        self.alive = True
        self.queue = Queue()
        self.count = 0

    def start(self):
        for i in range(2):
            process = Process(target=self.process)
            process.start()
            self.threads.append(process)

        while self.alive or [process for process in self.threads if process.is_alive()]:
            for i in range(10):
                self.queue.put(i)
                time.sleep(1)

    def process(self):
        while self.alive:
            try:
                item = self.queue.get_nowait()
                self.count += item
            except Empty:
                continue
            print("%s get item from main process. %s, %s"%(os.getpid(), self, self.count))

    def stop(self, *args):
        print ("%s stop. "%os.getpid())
        if self.pid == os.getpid():
            super(A, self).stop(*args)
        else:
            self.alive = False


if __name__ == "__main__":
    a = A()
    a.start()