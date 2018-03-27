# -*- coding:utf-8 -*-
import os
import sys

from celery import Celery
from toolkit import chain_all, load_module
from toolkit.managers import ExceptContext, Timer

app = Celery('tasks')
app.config_from_object("settings")


def get_convert_engine(engine=[]):
    """
        用来保证ImageProcess的单例性
    """
    if not engine:
        ic = load_module("utils.image_process").ImageProcess("settings")
        engine.append(ic)
    return engine[-1]


@app.task
def process_images(item):
    """
    图片处理函数， 使用图片处理类对图片进行处理
    :param item: 图片相关信息集合
    :return: 处理结果
    """
    msg = dict()

    with ExceptContext():
        with Timer() as timer:
            sys.path.insert(0, os.getcwd())
            image_process = get_convert_engine()
            spider = item.get("spiderid")
            crawlid = item.get("crawlid")
            product_id = item.get("product_id")
            image_process.logger.info("Process in image convert engine, spider: %s, crawlid: %s, product_id: %s. " % (
                spider, crawlid, product_id))
            result = image_process.process_image(spider, item)
            if isinstance(result, bool):
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
        msg["cost"] = timer.cost
        msg["start_process"] = timer.start
        msg["end_process"] = timer.stop

    return msg