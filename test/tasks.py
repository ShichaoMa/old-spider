# -*- coding:utf-8 -*-
from celery import Celery


app = Celery('tasks')

app.config_from_object("celeryconfig")



@app.task
def add(x, y):
    return x + y

@app.task
def error_handler(uuid):
    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
        uuid, exc, result.traceback))