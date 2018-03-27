#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import time
import socket
import select
import traceback
import threading

from PIL import Image
from io import BytesIO
from queue import Queue, Empty
from argparse import ArgumentParser

from toolkit.daemon_ctl import common_stop_start_control
from toolkit.manager import ExceptContext

from utils.core import Monitor
from utils.amazon_captcha import binarized


class Recognition(Monitor):
    """
        amazon专用验证码识别程序
    """
    name = "recognition"

    def __init__(self, settings):
        super(Recognition, self).__init__(settings)
        self.readable = Queue()
        self.host = self.settings.get("CAPTCHA_RECOGNITION_HOST")
        self.port = self.settings.get_int("CAPTCHA_RECOGNITION_PORT")
        self.server = None
        self.callback = binarized

    def manual(self, buf):
        """手动处理验证码"""
        img = Image.open(BytesIO(buf))
        img.show()
        alphabet = input("Please input the captcha words: ")
        return alphabet

    def setup(self):
        self.server = socket.socket()
        self.server.bind((self.host, self.port))
        print("Recognization server starting up ...")
        print("Listening on http://%s:%d/" % (self.host, self.port))
        print("Hit Ctrl-C to quit.")
        self.server.listen(10)
        t = threading.Thread(target=self.poll_queue)
        self.children.append(t)
        t.start()

    def poll_queue(self):
        """
            子线程从验证码通道里取出客户端socket进行验证码识别
        """
        while self.alive or self.readable.qsize():
            now = time.time()
            with ExceptContext(Exception, errback=self.log_err):
                try:
                    client, addr, t = self.readable.get_nowait()
                except Empty:
                    self.logger.debug("No client. ")
                    time.sleep(1)
                    continue
                if now-t > 20:
                    self.logger.debug("Abandon client from %s:%s. "%addr)
                else:
                    self.recognize(client, addr, t)
                client.close()

    def start(self):
        """
            将接收到的socket链接放入验证码通道交付给子进程处理
        """
        try:
            self.setup()
            while self.alive or [x for x in self.children if x.is_alive()]:
                with ExceptContext(Exception, errback=self.log_err):
                    rd_lst, _, _ = select.select([self.server], [], [], 0.1)
                    if not rd_lst:
                        time.sleep(1)
                    for rd in rd_lst:
                        client, addr = rd.accept()
                        self.readable.put((client, addr, time.time()))
        finally:
            if self.server:
                self.server.close()

    def recognize(self, client, addr, t):
        """
            接收验证码字节流，并判断是否超时，如果超时60，则丢弃，否则返回处理结果
        """
        with ExceptContext(Exception, errback=self.log_err):
            self.logger.debug("Receive captcha from %s:%s. " % addr)
            buf = client.recv(102400)
            alphabet = self.callback(buf)
            if time.time()-t > 60:
                self.logger.info("Time out. ")
            else:
                if isinstance(alphabet, str):
                    alphabet = alphabet.encode("utf-8")
                client.send(alphabet)
                self.logger.info("Send result:%s to %s:%s. "%((alphabet, )+addr))

    @classmethod
    def run(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", default="settings.py")
        from settings import BASENAME, LOG_DIR
        # 这个log是代替的标准输出和标准错误
        monitor_log_path = os.path.join(BASENAME, LOG_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")
        args = common_stop_start_control(parser, monitor_log_path, 2)
        rg = cls(args.settings)
        rg.set_logger()
        rg.start()


if __name__ == "__main__":
    Recognition.run()