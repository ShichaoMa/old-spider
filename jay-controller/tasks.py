# -*- coding:utf-8 -*-
from celery import Celery

app = Celery('tasks')
app.config_from_object("settings")


@app.task
def process_images(item):
    """
    图片处理函数， 使用图片处理类对图片进行处理
    :param item: 图片相关信息集合
    :return: 处理结果
    """
    return item