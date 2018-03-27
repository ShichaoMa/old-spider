# -*- coding:utf-8 -*-
import os
import json

from celery import Celery
from toolkit import timeout
from toolkit.translator import Translator
from toolkit.managers import ExceptContext, Timer
from toolkit.logger import Logger
from toolkit.settings import SettingsLoader

from .converter import Converter

settings = SettingsLoader().load("settings")


class Engine(object):
    logger = Logger(settings, "celery_%s" % os.getpid())

    def __init__(self, *engines):

        self.engines = engines

    def __getattr__(self, item):
        for engine in self.engines:
            func = getattr(engine, item, None)
            if func:

                return func

app = Celery('tasks')
app.config_from_object("settings")

translator = Translator(settings).__enter__()

engine = Engine(Converter(settings), translator)


def timeout_wrapper(ar):
    ar.delay = timeout(10, False)(ar.delay)
    return ar


@timeout_wrapper
@app.task
def convert(item):
    """
    图片处理函数， 使用图片处理类对图片进行处理
    :param item: 图片item
    :return: 处理结果
    """

    with ExceptContext() as ec:
        images = dict()
        with Timer() as timer:
            images = engine.convert(item)
    images["trace"] = dict()
    images["trace"]["cost"] = timer.cost
    images["trace"]["start_process"] = timer.start
    images["trace"]["end_process"] = timer.stop
    if "result" not in images and not ec.got_err:
        images["result"] = True
    elif ec.got_err:
        images["result"] = False

    return images


@timeout_wrapper
@app.task
def translate(item):
    """
    翻译函数，对英文描述等信息进行翻译
    :param item: 翻译item
    :return: 处理结果
    """
    data = {}
    with ExceptContext():
        with Timer() as timer:
            cn = engine.translate(item.pop("values"))
            if not cn and item["en"]:
                data["result"] = False
            else:
                data["result"] = True
                if item["item_type"].count("Features"):
                    item["cn"] = json.dumps(cn.split("<1>"))
                elif item["item_type"].count("Specs"):
                    tags = cn.split("<1>")
                    item["cn"] = json.dumps([(tags[i], tags[i + 1]) for i in range(0, (len(tags) // 2) * 2, 2)])
                else:
                    item["cn"] = cn
        data["items"] = [item]
        data["trace"] = dict()
        data["trace"]["cost"] = timer.cost
        data["trace"]["start_process"] = timer.start
        data["trace"]["end_process"] = timer.stop

    return data