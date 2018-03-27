#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import time
import json
import hashlib

from redis import Redis
from subprocess import Popen
from threading import Thread
from urllib.parse import urlparse
from os.path import splitext, basename

from toolkit import load_function as load_class
from toolkit.managers import ExceptContext


class ImageItemFilter(load_class("components.ItemFilter")):
    """
        对explore类型的图片进行图片处理
    """
    name = "image_item_filter"

    def __init__(self):
        super(ImageItemFilter, self).__init__()
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT", 6379))
        self.convert_in_queue = "convert_in_queue"
        self.convert_out_queue = "convert_out_queue"
        self.cmd = ("./image_filter_worker.py", "-iq", self.convert_in_queue, "-oq", self.convert_out_queue)

    def start(self):
        for download_process in range(self.settings.get_int("IMAGE_PROCESSES", 10)):
            process = Popen(self.cmd)
            self.children.append(process)
        control_process_thread = Thread(target=self.control_process)
        control_process_thread.setDaemon(True)
        control_process_thread.start()
        while self.alive or [process for process in self.children if process.poll() is None]:
            with ExceptContext(Exception, errback=self.log_err):
                result_message = message = self.hook()
                if not message:
                    self.logger.debug("Haven't got hook message. ")
                    message = self.consume() if self.alive else None
                    if not message:
                        time.sleep(2)
                        continue
                    else:
                        self.logger.debug("Process message. ")
                        result_message = self.process_message(message)
                if not result_message:
                    self.logger.debug("Ignore produce message. ")
                    continue
                self.produce(result_message)

    def control_process(self):
        while self.alive:
            for index, process in enumerate(self.children):
                if process.poll() is None:
                    continue
                else:
                    process.terminate()
                    process.wait()
                    self.logger.debug("Process %s is dead restart again. "%self.cmd[0])
                    self.children[index] = Popen(self.cmd)
            time.sleep(1)

    def hook(self):
        """
        主线程轮循时执行该函数，当该函数返回信息时，将该信息发送kafka，当信息为空时，
        从消费者消费信息并process
        :return: 处理结果集
        """
        message = self.redis_conn.rpop(self.convert_out_queue)
        if message:
            item = json.loads(message)
            if not item.get("convert_result"):
                self.logger.error("Error in convert image. Error: %s"%item.get("convert_failed_reason"))
            self.logger.info("Send explore message crawlid: %s, spiderid: %s to kafka successful. " % (
                item.get("crawlid"), item.get("spiderid")))
            return message

    def process_message(self, message):
        """
        处理item
        :param message:
        :return:
        """
        with ExceptContext(Exception, errback=self.log_err):
            item = json.loads(message)
            crawlid = item.get("crawlid")
            spiderid = item.get("spiderid")
            if item.get("seed") or item.get("meta", {}).get("type") == "explore":
                if self._process_item_images(item):
                    return
                self.logger.info("Send explore message crawlid: %s, spiderid: %s "
                                 "without images to kafka topic: %s successful" %(crawlid, spiderid, self.topic_out))
            else:
                self.logger.info("Send update message crawlid: %s, spiderid: %s "
                                 "to kafka topic: %s successful" %(crawlid, spiderid, self.topic_out))
            return message

    def _process_item_images(self, item):
        """
        处理item的图片
        :param item:
        :return:
        """
        image_urls = item.get("image_urls", [])
        if len(image_urls) > 0:
            images = []
            # 将amazon 和loco_amazon的图片保存到同一目录下
            spiderid = item['spiderid'].replace("loco_", "")
            for url in image_urls:
                filename, file_ext = splitext(basename(urlparse(url).path))
                if not file_ext:
                    file_ext = ".jpg"
                else:
                    file_ext = file_ext.lower()
                out_file_name = "%s/%s/%s%s" % (
                    self.settings.get("IMAGES_STORE"), spiderid, hashlib.sha1(url.encode("utf-8")).hexdigest(),
                    file_ext)
                images.append({'url': url, 'path': out_file_name, "origin": True})
            item['images'] = images
            del item["image_urls"]
            self.redis_conn.lpush(self.convert_in_queue, json.dumps(item))
            self.logger.info("Process item to image convert, "
                             "the rest item count is: %s. " % self.redis_conn.llen(self.convert_in_queue))
            return True

    def stop(self, *args):
        """
        关闭所有线程，进程和资源
        """
        super(ImageItemFilter, self).stop(*args)
        for process in self.children:
            process.terminate()

    def stop_child(self, child):
        # 直接通过终端启动controller进程，在关闭的时候,controller进程向filter发送关闭信号
        # 与此同时终端会向所有子进程发送信号，导致filter收到了两次关闭，因此采取了强关操作
        # 而第一次stop的时候，filter下面的子进程已经关闭了，所以强关子进程会导致出错
        # 因此不推荐使用终端直接启动controller进程
        child.kill()


if __name__ == "__main__":
    ImageItemFilter().start()