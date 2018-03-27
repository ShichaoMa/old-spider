# -*- coding:utf-8 -*-
import os
import time
import glob
import pymongo
import argparse

from redis import Redis
from threading import Thread
from bottle import get, template, Jinja2Template, request, redirect, static_file, run, app
from log_to_kafka import Logger

from crawler import Crawler


class KeyWordServer(Logger):

    name = "KeyWordServer"

    def __init__(self, settings):
        super(KeyWordServer, self).__init__(settings)
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get("REDIS_PORT"))
        self.conn = pymongo.MongoClient(
            self.settings.get("MONGODB_HOST"),
            self.settings.get("MONGODB_PORT"))[self.settings.get("DB")][self.settings.get("COLLECTION")]
        self.register()
        self.run()

    def register(self):
        get('/search')(self.search)
        get('/')(self.index)
        get('/download/<id:re:\d+>')(self.download)

    def run(self):
        self.set_logger()
        run(host=self.settings.get("HOST"), port=self.settings.get("PORT"))

    def search(self):
        id = time.strftime("%Y%m%d%H%M%S")
        keyword = request.GET.get("keyword")
        num = request.GET.get("num")

        if keyword and num:
            crawler = Crawler(self.settings, keyword, num, id, self.conn)
            crawler.set_logger(self.logger)
            Thread(target=crawler.start).start()
            self.redis_conn.hmset(("%s%%s"%self.settings.get("PRODUCT_PREFIX"))%id, {"id": id, "keyword": keyword, "num": num})
            self.redis_conn.expire(("%s%%s"%self.settings.get("PRODUCT_PREFIX"))%id, 5*24*60*60)
            redirect('/')
        else:
            return self.index("必须给出关键字和页数！".decode("utf-8"))

    def download(self, id):
        files = glob.glob("task/*_%s.txt"%id)
        if len(files) != 2:
            return self.index("缺少文件，请联系管理员. ".decode("utf-8"))
        else:
            if not os.path.exists("temp"):
                os.mkdir("temp")
            file_name = "temp/result_%s.zip"%id
            files.insert(0, file_name)
            os.system("zip -rq  %s %s %s"%tuple(files))
            return static_file(file_name, ".", download=True)

    def index(self, errors=None):
        records = []
        keys = self.redis_conn.keys("%s*"%self.settings.get("PRODUCT_PREFIX"))

        for key in keys:
            id = key.split("_")[-1]
            data = {"id": id}

            if os.path.exists('task/where_%s.txt'%id) and os.path.exists('task/keywords_%s.txt'%id):
                self.redis_conn.hmset(key, {"finished": True})
            else:
                self.redis_conn.hmset(key, {"update_time": time.strftime("%Y%m%d%H%M%S"), "finished": False})
                self.redis_conn.expire(("%s%%s"%self.settings.get("PRODUCT_PREFIX")) % id, 5 * 24 * 60 * 60)

            d = self.redis_conn.hgetall(key)
            d['keyword'] = d['keyword'].decode("utf-8")
            data.update(d)
            records.append(data)

        return template(open("index.html").read().decode("utf-8"), errors=errors, records=sorted(records, key=lambda x: -int(x['id'])), template_adapter=Jinja2Template)

    @classmethod
    def parse_args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--settings", default="settings.py")
        return cls(**vars(parser.parse_args()))


if __name__ == "__main__":
    KeyWordServer.parse_args()
