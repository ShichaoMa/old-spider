# -*- coding:utf-8 -*-
import os
import sys
import time

from celery import Celery
from toolkit import chain_all
from toolkit.manager import ExceptContext

from . import get_convert_engine

app = Celery('tasks')
app.config_from_object("settings")


@app.task
def process_images(item):
    """
    图片处理函数， 使用图片处理类对图片进行处理
    :param item: 图片相关信息集合
    :return: 处理结果
    """
    msg = dict()
    t1 = time.time()

    def final(got_err, msg=msg):
        msg["cost"] = time.time() - t1
        msg["start_process"] = t1
        msg["end_process"] = time.time()

    with ExceptContext(finalback=final):
        sys.path.insert(0, os.getcwd())
        image_process = get_convert_engine()
        spider = item.get("spiderid")
        crawlid = item.get("crawlid")
        product_id = item.get("product_id")
        image_process.logger.info("Process in image convert engine, spider: %s, crawlid: %s, product_id: %s. " % (
            spider, crawlid, product_id))
        result = image_process.process_image(spider, item)
        if isinstance(result, Exception):
            msg["convert_result"] = False
            msg["convert_failed_reason"] = str(result)
        elif isinstance(result, bool):
            msg["convert_result"] = result
        else:
            for package in chain_all(result):
                package and package.pop("buffer", None)
            msg["convert_result"] = True
            msg["main_images"] = result[0]
            msg["error_images"] = result[1]
            for image_package in item["images"]:
                image_package.pop("buffer", None)
            msg["images"] = item["images"]
        image_process.logger.info(
            "Finish process in image convert engine, spider: %s, crawlid: %s, product_id: %s, result: %s" % (
                spider, crawlid, product_id, msg.get("convert_result", True)))
    return msg