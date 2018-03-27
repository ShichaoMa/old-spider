import requests
import traceback

from PIL import Image
from io import BytesIO
from hashlib import md5, sha1
from functools import partial
from urllib.parse import urljoin
from os.path import join, split

from toolkit import retry_wrapper, re_search
from toolkit.monitors import ProxyPool
from toolkit.managers import ExceptContext

from .pil_utils import crop_to, crop_to_center, convert_to


class SaveSeaweedError(Exception):
    pass


class InvalidateImageError(Exception):
    pass


class Converter(ProxyPool):
    name = "converter"
    image_funcs = [
        crop_to_center,
        partial(crop_to, position="top"),
        partial(crop_to, position="bottom"),
        partial(crop_to, position="right"),
        partial(crop_to, position="left"),
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self, settings):
        super(Converter, self).__init__(settings)
        self.session = requests.Session()
        self.session.post = retry_wrapper(
            self.settings.get_int("DOWNLOAD_RETRY_TIMES", 10),
            error_handler=self.save_error_handler)(self.session.post)
        self.download = retry_wrapper(
            self.settings.get_int("DOWNLOAD_RETRY_TIMES", 10),
            error_handler=self.download_error_handler)(self.download)
        self.cache_path = dict()

    def join_path(self, path):
        return self.cache_path.setdefault(path, urljoin(self.settings.get("IMAGES_STORE"), path))

    def convert(self, image):
        if requests.head(self.join_path(image["path"])).status_code < 300:
            buffer, img_obj = self.download(self.join_path(image["path"]), from_seaweed=True)
            if img_obj:
                image["fingerprint"] = md5(buffer).hexdigest()
                return self.generate_images(image, img_obj)
        buffer, img_obj = self.download(image["url"])
        new = BytesIO()
        if max(img_obj.size) < 800:
            convert_to(img_obj, "", 800, 800).save(new, "jpeg")
        elif image["url"].lower().endswith("png"):
            background = Image.new('RGB', img_obj.size, (255, 255, 255))
            background.paste(img_obj)
            background.save(new, "jpeg")
        else:
            new.write(buffer)
        new.seek(0)
        dir_name, base_name = split(self.join_path(image["path"]))
        resp = self.session.post(dir_name + "/", files={"file": (base_name, new)})
        if resp.status_code < 400:
            self.logger.debug("Successfully save %s. " % self.join_path(self.join_path(image["path"])))
        else:
            raise SaveSeaweedError(resp.text)
        image["fingerprint"] = md5(buffer).hexdigest()
        return self.generate_images(image, img_obj)

    def generate_images(self, image, img_obj):
        """
        提供处理后的 n 张图片
        :param main_image_package:
        :param n:
        :return:
        """
        image.pop("use_proxy", None)
        images = dict()
        images.setdefault("items", []).append(image)
        with ExceptContext(
                errback=lambda *args, images=images: self.errback(images, *args) or self.log_err(*args)):
            for i in range(6-image["image_count"]):
                new_image = image.copy()
                new_image["type"] = new_image["type"] + "_" + str(i) if image["type"] else new_image["type"]
                parts = new_image["item_id"].split("::")
                parts[-1] = new_image["type"] if image["type"] else parts[-1]
                new_image["item_id"] = "::".join(parts)
                new_image["init"] = False
                new_image["origin"] = False
                new_image["path"] = self.gen_path(
                    "/", re_search(r"/(\w+)/", image["path"]), new_image["url"] + str(i))
                # 0代表不缩放
                new = BytesIO()
                self.image_funcs[i](img_obj, new, 0, 0).convert('RGB').save(new, "jpeg")
                new.seek(0)
                if self.session.head(self.join_path(new_image["path"])).status_code >= 400:
                        dir_name, base_name = split(self.join_path(new_image["path"]))
                        resp = self.session.post(dir_name + "/", files={"file": (base_name, new)})
                        if resp.status_code < 400:
                            self.logger.debug(
                                "Successfully save new make pic %s. " % self.join_path(
                                    new_image["path"]))
                        else:
                            raise SaveSeaweedError(resp.text)
                else:
                    self.logger.debug("Image %s have exists. " % self.join_path(new_image["path"]))
                new.seek(0)
                new_image["fingerprint"] = md5(new.read()).hexdigest()
                images["items"].append(new_image)
        return images

    def make_sure_image_validate(self, buffer):
        """
        确定现存的图片是合法图片，否则删除其及其md5文件
        :param filename_or_buf:
        :return:
        """
        with ExceptContext(OSError, errback=self.log_err):
            return Image.open(BytesIO(buffer))

    def errback(self, images, func_name, *args):
        images["result"] = False
        images["failed_reason"] = "".join(traceback.format_exception(*args))
        if args[0] is OSError:
            self.session.delete(self.join_path(images["items"][0]["path"]))
            self.logger.debug("Remove image: %s. "%self.join_path(images["items"][0]["path"]))

    def download(self, url, from_seaweed=False):

        buffer, proxies = b"", None if from_seaweed else self.proxy_choice()
        self.logger.debug("Process %s with proxy: %s. "%(url, proxies))
        resp = self.session.get(url, headers=self.headers, proxies=proxies,
                                timeout=(self.settings.get("DOWNLOAD_TIMEOUT", 3),
                                         self.settings.get("DOWNLOAD_TIMEOUT", 3)+5))
        if resp.status_code < 300:
            for chuck in resp.iter_content(1024):
                buffer += chuck
            self.logger.debug(
                "Download %s finished. response code: %s, length: %s" % (
                    url, resp.status_code, len(buffer)))
        else:
            raise InvalidateImageError("Error response: %s. status code: %s" % (
                url, resp.status_code))

        img_obj = self.make_sure_image_validate(buffer)
        if img_obj:
            return buffer, img_obj
        else:
            if not from_seaweed:
                raise InvalidateImageError("Error image: %s. " % url)
            else:
                self.session.delete(url)
                self.logger.debug("Remove image: %s. " % url)
                return None, None

    @classmethod
    def gen_path(cls, base, spiderid, url):
        codec = cls.sha1_encode(url)
        return join(base, spiderid, "%s.jpg" % codec)

    @staticmethod
    def sha1_encode(string):
        return sha1(string.encode()).hexdigest()

    @staticmethod
    def md5_encode(string, count=6):
        return md5(string.encode()).hexdigest()[:count]

    def save_error_handler(self, func_name, retry_time, e, *args, **kwargs):
        self.logger.error(
            "Error in %s for retry %s times.  Error: %s" % (
                func_name, retry_time, e))

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
            self.logger.error(
                "Invalidate proxy error always retry. Error:%s" % e)
            return True
        else:
            self.logger.error("Error in %s for retry %s times. Error: %s" % (
                func_name, retry_time, e))


if __name__ == "__main__":
    convert = Converter("settings.py")
    convert.convert({"url": "https://d2cekp7jyosbti.cloudfront.net/web/files/collections/5a1535172b9f10.91321163.png", "path": "http://192.168.200.71:8888/aaa.jpg"})