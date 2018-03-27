# -*- coding:utf-8 -*-
import requests

from argparse import ArgumentParser
from psycopg2 import connect
from log_to_kafka import Logger


class Rocket(Logger):

    name = "rocket"

    def __init__(self, settings, site):
        super(Rocket, self).__init__(settings)
        self.conn = connect("dbname='upc' user='roc' host='192.168.200.94' password='roc'")
        self.cur = self.conn.cursor()
        #self.redis_conn = Redis(self.settings.get("REDIS_HOST", "192.168.200.94"), self.settings.get("REDIS_PORT", 6379))
        self.site = site
        self.jay_api = "http://%s:%s/api/update" % (
            self.settings.get("HOST", "192.168.200.37"),
            self.settings.get("PORT", 80))
        self.set_logger()

    def find(self):
        sql = "SELECT a.upc, a.ean, a.mpn, b.url From amazon_roc a, site_roc b WHERE a.upc=b.upc AND b.site=%s;"
        self.cur.execute(sql, (self.site, ))
        return self.cur.fetchall()

    def start(self):
        self.logger.debug("Start to find %s's url. "%self.site)
        rs = self.find()
        # data = []
        # for record in rs:
        #     if record[0] in self.redis_conn:
        self.logger.debug("Start send to jay api. ")
        data = {"is_site": True, "site": self.site.lower(), "urls": rs}
        resp = requests.post(self.jay_api, json=data)
        self.logger.debug("Jay api response code: %s"%resp.status_code)

    @classmethod
    def parse_args(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", default="settings.py")
        parser.add_argument("site", nargs="?")
        return cls(**vars(parser.parse_args()))


if __name__ == "__main__":
    Rocket.parse_args().start()