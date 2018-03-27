# -*- coding:utf-8 -*-
import re
import time
import requests
import datetime
import traceback

from os import getpid
from PIL import Image
from io import BytesIO
from hashlib import sha1, md5
from functools import partial, wraps
from queue import Queue, Empty
from threading import Thread, RLock
from os.path import dirname, basename
from urllib.parse import urlparse, urlunparse

from toolkit.managers import ExceptContext
from toolkit.monitors import ProxyPool
from toolkit import retry_wrapper, get_ip, LazyDict

from .convert_config import CONVERTIONS
from .pil_utils import crop_to, crop_to_center

class InvalidateImageError(Exception):
    pass


class Session(requests.Session):
    #
    # #@wrapper
    # def head(self, url, **kwargs):
    #     return super(Session, self).head(url, **kwargs)
    #
    # #@wrapper
    # def post(self, url, data=None, json=None, **kwargs):
    #     return super(Session, self).post(url, data=None, json=None, **kwargs)
    pass


class ImageProcess(ProxyPool):
    """
        图片下载处理程序主类
    """
    name = "image_process"
    # 每种颜色图片需要的张数，不够继续生成
    g_required_images_count = 6

    def __init__(self, settings):
        super(ImageProcess, self).__init__(settings)
        self.image_funcs = [
            crop_to_center,
            partial(crop_to, position="top"),
            partial(crop_to, position="bottom"),
            partial(crop_to, position="right"),
            partial(crop_to, position="left"),
        ]
        self.session = Session()
        self.pid = getpid()
        self.ip = get_ip()
        self.name = "%s-%s-%s" % (self.name, self.ip, self.pid)
        self.normal_pics_width = [150, 640, 800]
        self.threads = []
        self.lock = RLock()
        self.pic_count = 0
        self.download_queue = Queue()
        for i in range(self.settings.get_int("IMAGE_DOWNLOAD_THREADS", 20)):
            t = Thread(target=self.download)
            t.setDaemon(True)
            t.start()
            self.threads.append(t)

    def process_image(self, spider, document):
        error_messages = self.process_download(document)
        if spider == "loco_amazon":
            return True
        if not isinstance(error_messages, list):
            error_messages = []
        return self.generate_convert(CONVERTIONS.get(spider, {}))(document, error_messages)

    def process_download(self, document):
        """
        对每一个document中的一个图片放到下载队列进行下载
        :param document:
        :return:
        """
        error_packages = list()
        with ExceptContext(errback=self.log_err) as ec:
            for image_package in document.get("images", []):
                if image_package:
                    self.download_queue.put((image_package, error_packages))
                    self.lock.acquire()
                    self.pic_count += 1
                    self.lock.release()
            while self.pic_count > 0:
                time.sleep(0.1)
        return not ec.got_err or error_packages

    def download(self):
        """
        子线程实例，从下载队列中取出图片，并进行图片下载
        :return:
        """
        error_packages = None
        session = Session()

        def _final(got_err):
            with self.lock:
                self.pic_count -= 1

        while True:
            try:
                image_package, error_packages = self.download_queue.get_nowait()
            except Empty:
                image_package = None
            if image_package:
                with ExceptContext(errback=self.log_err, finalback=_final):
                    filename = image_package.get("path")
                    url = image_package.get("url")
                    # if make_sure_image_validate(filename):
                    # 因为在下载保存到磁盘之前，已经做过是否为图片的检查，所以不需要再检查了
                    if session.head(filename).status_code < 400:
                        self.logger.debug("File: %s is already exists. "%filename)
                        md5_file_name = self.get_md5_filename(filename)
                        if session.head(md5_file_name).status_code >= 400:
                            buffer = b""
                            for chunk in requests.get(filename, stream=True).iter_content(1024):
                                buffer += chunk
                            if session.head(md5_file_name).status_code >= 400:
                                resp = session.post(dirname(md5_file_name) + "/",
                                             files={"file": (basename(md5_file_name), BytesIO(md5(buffer).hexdigest().encode("utf-8")))})
                                self.logger.debug("Write md5 to file: %s. status code: %s" % (md5_file_name, resp.status_code))
                        continue
                    times = self.settings.get_int("DOWNLOAD_RETRY_TIMES", 3)
                    try:
                        result = retry_wrapper(times, error_handler=self.download_error_handler)(
                            self._download)(url, filename, session)
                    except Exception:
                        self.logger.error("After retry %s times the image path: %s, url: %s still cannot download. "
                                          "Error: %s"%(times, filename, url, traceback.format_exc()))
                        result = False
                    if result:
                        image_package["buffer"] = result
                        if session.head(filename).status_code >= 400:
                            # 写入文件
                            resp = session.post(dirname(filename) + "/",
                                         files={"file": (basename(filename), BytesIO(image_package["buffer"]))})
                            if resp.status_code < 400:
                                self.logger.debug("Write buffer to file: %s. response code: %s"%(filename, resp.status_code))
                                continue
                            else:
                                self.logger.error("File: %s write error: %s"%(filename, resp.text))
                    with self.lock:
                        error_packages.append(image_package)
                    self.error_back(filename)
            else:
                time.sleep(0.1)

    def _download(self, url, filename, session):
        """
        下载函数实现
        :param url: 下载url
        :return: True成功，False失败
        """
        #########################临时代码##########################################
        # nas_file = filename.replace("http://192.168.200.71:8888/", "/mnt/nas69/")
        # if exists(nas_file) and getsize(nas_file):
        #     self.logger.debug("%s is exist in nas. upload to seaweed. "%nas_file)
        #     buffer = open(nas_file, "rb").read()
        # else:
        #########################################################################
        buffer = bytes()
        proxies = self.proxy_choice()
        headers = self.settings.get("HEADERS")
        self.logger.debug("Use proxy: %s to download images from %s. "%(proxies, url))
        resp = session.get(url, headers=headers, stream=True,
                            timeout=self.settings.get_int("DOWNLOAD_TIMEOUT", 5), proxies=proxies)
        if resp.status_code <= 300:
            for chunk in resp.iter_content(chunk_size=1024):
                buffer += chunk
        else:
            raise requests.HTTPError("Invalidate response code: %s. proxy: %s"%(resp.status_code, proxies["http"]))
        if not self.make_sure_image_validate(BytesIO(buffer), True):
            raise InvalidateImageError("Invalidate Image")
        md5_file_name = self.get_md5_filename(filename)
        if session.head(md5_file_name).status_code >= 400:
            resp = session.post(dirname(md5_file_name) + "/",
                                files={"file": (basename(md5_file_name), BytesIO(md5(buffer).hexdigest().encode("utf-8")))})
            self.logger.debug("Write md5 to file: %s. status code: %s" % (md5_file_name, resp.status_code))
        return buffer

    def download_error_handler(self, func_name, retry_time, e, *args, **kwargs):
        """
        error_handler实现参数
        :param func_name: 重试函数的名字
        :param retry_time: 重试到了第几次
        :param e: 需要重试的异常
        :param args: 重试参数的参数
        :param kwargs: 重试参数的参数
        :return: 当返回True时，该异常不会计入重试次数
        """
        if isinstance(e, requests.exceptions.ProxyError):
            self.logger.error("Invalidate proxy error always retry. "
                              "Error:%s" % e)
            return True
        else:
            self.logger.error("Error in %s for retry %s times. "
                              "Error: %s"%(func_name, retry_time, e))

    @staticmethod
    def error_back(filename):
        pass

    # 这个地方曾经引发严重错误，在增加error_packages参数之后，由于default所指向的lambda函数未增加，导致在处理loco等没有
    # convert配置的网站图片时，引发参数数量不匹配的错误，同时发现了另一个错误，对partial产生的方法，可以使用func.func来
    # 获取被包装的func, 所以，即使是lambda，也应该使用partial进行包装一下，以统一调用接口。
    def generate_convert(self, meta, default=partial((lambda document, error_packages, is_main: True), is_main=None)):
        """
        根据网站生成相应的转换函数
        :param meta:
        :param default:
        :return:
        """
        if meta is None:
            return default
        return partial(self.process_convert, is_main=meta.get("is_main") or self.is_main,
                       position=meta.get("position") or self.position)

    def process_convert(self, document, error_packages, is_main, position):
        """
        判断是多颜色还是单色
        :param document:
        :param is_main:
        :param position:
        :return:
        """
        with ExceptContext(errback=self.log_err):
            for error_package in error_packages:
                if error_package in document["images"]:
                    document["images"].remove(error_package)

            result = getattr(self, "process_%s_color_images"% ("multi" if document.get("color_images") else "one"))\
                (document.get("color_images"),
                 document["images"],
                 is_main=is_main, position=position)
            return result, error_packages

    def process_multi_color_images(self, color_images, total_images, is_main, position):
        """
        处理多个颜色的document
        :param color_images: document["color_images"]
        :param total_images: document["images"]
        :param is_main:
        :param position:
        :return:
        """
        main_image_packages = []
        for one_color_images in color_images.values():
            main_image_packages.extend(
                self.process_one_color_images(one_color_images, total_images, is_main=is_main, position=position))
        return main_image_packages

    def process_one_color_images(self, one_color_images, total_images, is_main, position):
        """
        每个颜色图片的处理函数
        :param total_images: document["images"]
        :param one_color_images:  每个颜色的image_url集合
        :param main: 主图识别方式
        :param position: 从one_color_images中的每个元素中找到图片的url
        :return:
        """
        main_found = False
        same_color_images_count = 0
        main_image_package = None
        iter_color_images = [x["url"] for x in total_images] if one_color_images is None else one_color_images
        for image in iter_color_images:
            image_package = self.get_image_package(total_images, position(image))
            if image_package:
                image_package = LazyDict(image_package, self.turn)
                main_image_package = main_image_package or image_package
                # 主图判断结果是一个列表，按主图可能性从高到低排列
                # 主图可能性列表中的结果集是互斥的，只可能返回一个True结果，返回结果可能是[True, False...]
                # 若主图可能性最高的结果返回为True，则认为主图已找到，设置main_found为True，之后无需再进行任何判断，直接break
                # 每次找到一张可能主图即m=True时，都可中断当前循环
                for i, m in enumerate(is_main(image)):
                    if main_found:
                        break
                    if m:
                        main_image_package = image_package or main_image_package
                        if i == 0:
                            main_found = True
                        break
                same_color_images_count += 1
        total_images.extend(
            dict(url=main_image_package.get("url"), path=path, origin=False) for path in
            self.generate_images(main_image_package, self.g_required_images_count - same_color_images_count))
        return [main_image_package and main_image_package.to_dict()]

    def get_image_package(self, images, url_or_pattern):
        for image in images:
            if image['url'] == url_or_pattern:
                return image
            if not isinstance(url_or_pattern, str):
                if url_or_pattern.search(image['url']):
                    return image
        self.logger.error("%s is not download! " % url_or_pattern)

    def turn(self, image_package):
        buffer = bytes()
        for chunk in self.session.get(image_package["path"], stream=True).iter_content(chunk_size=1024):
            buffer += chunk
        return buffer

    def generate_images(self, main_image_package, n):
        """
        提供处理后的 n 张图片
        :param main_image_package:
        :param n:
        :return:
        """
        if main_image_package is None:
            self.logger.error("main_image_package is None! ")
            return []

        image_src = main_image_package["path"]
        f = None
        new_image_paths = []
        with ExceptContext(errback=self.log_err):
            for i in range(n):
                dest_path = image_src[:image_src.rfind('.')] + '_'+ str(i + 1) + '.jpg'
                out_file_name_base = sha1(dest_path.encode("utf-8")).hexdigest()
                dest_path = '%s/%s' % (re.search(r"(%s/\w+)/" % self.settings.get(
                    "IMAGES_STORE"), dest_path).group(1), "%s%s" % (out_file_name_base, ".jpg"))
                new_image_paths.append(dest_path)
                if self.session.head(dest_path).status_code >= 400:
                    f = f or Image.open(BytesIO(main_image_package["buffer"]))
                    #  0代表不缩放
                    new = BytesIO()
                    self.image_funcs[i](f, new, 0, 0).save(new, "jpeg")
                    new.seek(0)
                    md5_file_name = self.get_md5_filename(dest_path)
                    if self.session.head(md5_file_name).status_code >= 400:
                        resp = self.session.post(dirname(md5_file_name) + "/",
                                            files={"file": (
                                            basename(md5_file_name), BytesIO(md5(new.read()).hexdigest().encode("utf-8")))})
                        self.logger.debug("Write md5 to file: %s. status code: %s" % (md5_file_name, resp.status_code))
                        new.seek(0)
                    if self.session.head(dest_path).status_code >= 400:
                        self.session.post(dirname(dest_path) + "/", files={"file": (basename(dest_path), new)})
                else:
                    self.logger.debug("Image %s have exists. " % dest_path)
        return new_image_paths

    def make_sure_image_validate(self, bytesio, dont_close=False):
        """
        确定现存的图片是合法图片，否则删除其及其md5文件
        :param filename_or_buf:
        :return:
        """
        with ExceptContext(OSError, errback=lambda *args: True):
            img = Image.open(bytesio)
            if not dont_close:
                img.close()
            return True

    def get_md5_filename(self, filename):
        md5_dir = self.settings.get("MD5_DIR", "/md5")
        parts = urlparse(filename)
        return urlunparse(parts._replace(path=md5_dir + parts.path.replace(".jpg", ".md5")))

    @staticmethod
    def is_main(image):
        return [False]

    @staticmethod
    def position(image):
        return image


if __name__ == "__main__":
    ip = ImageProcess("convert_config")
    ip.process_multi_color_images()