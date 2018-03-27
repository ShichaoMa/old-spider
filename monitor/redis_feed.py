# -*- coding:utf-8 -*-
import sys
import pickle
import json
import time
import argparse
import traceback


class RedisFeed(object):
    """
        任务投放
    """
    def __init__(self, crawlid, spiderid, url, urls_file, multiple, update, priority, port, host, full_url, custom, show=True, meta=None):
        self.name = "redis_feed"
        self.crawlid = crawlid
        self.spiderid = spiderid
        self.url = url
        self.urls_file = urls_file
        self.multiple = multiple
        self.update = update
        self.priority = priority
        self.port = port
        self.host = host
        self.full_url = full_url
        self.custom = custom
        self.show = show
        self.inc = 0
        self.meta = meta
        self.setup()

    @classmethod
    def parse_args(cls):

        parser = argparse.ArgumentParser(description="usage: %prog [options]")
        parser.add_argument('-rh', "--redis-host", dest="host", type=str, default="127.0.0.1", help="Redis host to feed in. ")
        parser.add_argument('-rp', "--redis-port", dest="port", type=int, default=6379, help="Redis port to feed in. ")
        parser.add_argument('-u', '--url', type=str, help="The url to crawl, a list of products. ")
        parser.add_argument('-uf', '--urls-file', type=str, help="The urlsfile to crawl, single product. ")
        parser.add_argument('-m', '--multiple', action="store_true", help="Multi list of products. ")
        parser.add_argument('-fl', '--full-url', action="store_true", help="Use the full url whether or not. . ")
        parser.add_argument('--update', action="store_true", help="Update products message, do not download images. ")
        parser.add_argument('-c', '--crawlid', type=str, help="An unique Id for a crawl task. ")
        parser.add_argument('-s', '--spiderid', required=True, type=str, help="The website you wanna crawl. ")
        parser.add_argument('-p', '--priority', type=int, default=100, help="Feed in the task queue with priority. ")
        parser.add_argument('--custom', action="store_true", help="Use the custom redis whether or not. ")
        return cls(**vars(parser.parse_args()))

    def setup(self):
        self.failed_count = 0

        if self.custom:
            from custom_redis.client import Redis
        else:
            from redis import Redis

        self.redis_conn = Redis(host=self.host, port=self.port)
        if self.crawlid:
            self.clean_previous_task(self.crawlid)
        self.crawlid = self.crawlid or time.strftime("%Y%m%d%H%M%S")

    def clean_previous_task(self, crawlid):
        failed_keys = self.redis_conn.keys("failed_download_*:%s"%crawlid)
        for fk in failed_keys:
            self.redis_conn.delete(fk)

        self.redis_conn.delete("crawlid:%s" % crawlid)
        self.redis_conn.delete("crawlid:%s:model" % crawlid)

    def build_url(self, line, spiderid):
        if not line:
            return
        stuffix = "com"
        if spiderid.startswith('amazon'):
            if spiderid != "amazon":
                spiderid, stuffix = spiderid.split(".", 1)
            return 'https://www.amazon.%s/gp/product/%s/ref=twister_dp_update?ie=UTF8&psc=1' % (
            stuffix, line.strip())
        elif spiderid == 'eastbay':
            return 'http://www.eastbay.com/product/model:%s' % line.strip()
        elif spiderid == 'finishline':
            return 'http://www.finishline.com/store/catalog/product.jsp?productId=%s' % line.strip()
        elif spiderid == 'drugstore':
            return 'http://www.drugstore.com/products/prod.asp?pid=%s' % line.strip()
        elif spiderid == 'zappos':
            return 'https://www.zappos.com/product/%s' % line.strip()
        elif spiderid == '6pm':
            return 'https://www.6pm.com/product/%s' % line.strip()
        elif spiderid == 'ashford':
            return 'http://www.ashford.com/us/%s.pid' % line.strip()

    def start(self):

        success_rate, failed_rate = 0, 0

        if isinstance(self.urls_file, str):
            self.urls_file = open(self.urls_file)

        if self.urls_file and self.multiple:
            # 多分类抓取
            with self.urls_file as f:
                lst = set(x for x in f.readlines() if x.strip())
                lines_count = len(lst)
                for index, line in enumerate(lst):
                    if line.strip("\357\273\277\r\n"):
                        crawlid, url = line.strip("\357\273\277\r\n").split("    ")
                        json_req = '{"url":"%s", "crawlid":"%s","spiderid":"%s","callback":"parse", "priority":%s}' % (
                            url.strip(),
                            crawlid,
                            self.spiderid,
                            self.priority
                        )
                        result = self.feed(self.get_name(url), json_req)
                        self.failed_count += result
                        success_rate, failed_rate = self.show_process_line(lines_count, index + 1, self.failed_count)
                        self.clean_previous_task(crawlid)
                        self.redis_conn.hmset("crawlid:%s" % crawlid, {
                            "spiderid": self.spiderid,
                            "type": "explore",
                            "priority": self.priority,
                        })
                        self.redis_conn.expire("crawlid:%s" % crawlid, 2 * 24 * 60 * 60)
        # 更新抓取
        elif self.urls_file and self.update:
            if self.spiderid.startswith("amazon."):
                self.id = "amazon"
            else:
                self.id = self.spiderid

            with self.urls_file as f:
                lst = set(x for x in f.readlines() if x.strip())
                lines_count = len(lst)
                queue = None
                for index, line in enumerate(lst):
                    url = line.strip("\357\273\277\r\n") if self.full_url else self.build_url(
                        line.strip("\357\273\277\r\n"),
                        self.spiderid)
                    if url:
                        json_req = '{"url":"%s", "crawlid":"%s","spiderid":"%s","callback":"parse_item", "errback":"errback", "priority":%s}' % (
                            url,
                            self.crawlid,
                            self.id,
                            self.priority
                        )
                        result = self.feed(queue or self.get_name(url), json_req)
                        self.failed_count += result
                        success_rate, failed_rate = self.show_process_line(lines_count, index + 1,
                                                                          self.failed_count)
                self.redis_conn.hmset("crawlid:%s" % self.crawlid, {
                    "spiderid": self.id,
                    "total_pages":lines_count,
                    "type": "update",
                    "priority": self.priority,
                })
                self.redis_conn.expire("crawlid:%s" % self.crawlid, 2*24*60*60)
        # item抓取
        elif self.urls_file:
            with self.urls_file as f:
                lst = set(x for x in f.readlines() if x.strip())
                lines_count = len(lst)
                for index, url in enumerate(lst):
                    json_req = '{"url":"%s","crawlid":"%s","spiderid":"%s","callback":"parse_item", "errback":"errback", "priority":%s, "seed": "true"}' % (
                        url.strip("\357\273\277\r\n"),
                        self.crawlid,
                        self.spiderid,
                        self.priority
                    )
                    self.failed_count += self.feed(self.get_name(url), json_req)
                    success_rate, failed_rate = self.show_process_line(lines_count, index + 1, self.failed_count)
                self.redis_conn.hmset("crawlid:%s" % self.crawlid, {
                    "spiderid": self.spiderid,
                    "total_pages": lines_count,
                    "type": "explore",
                    "priority": self.priority,
                })
                self.redis_conn.expire("crawlid:%s" % self.crawlid, 2 * 24 * 60 * 60)
        # 分类抓取
        elif self.url:
            url_list = self.url.split("     ")
            lines_count = len(url_list)
            for index, url in enumerate(url_list):
                json_req = '{"url":"%s","crawlid":"%s","spiderid":"%s","callback":"parse","priority":%s}' % (
                    url.strip(),
                    self.crawlid,
                    self.spiderid,
                    self.priority,
                )
                self.failed_count += self.feed(self.get_name(url), json_req)
                success_rate, failed_rate = self.show_process_line(lines_count, index + 1, self.failed_count)
            self.redis_conn.hmset("crawlid:%s" % self.crawlid, {
                "spiderid": self.spiderid,
                "type": "explore",
                "priority": self.priority,
            })
            self.redis_conn.expire("crawlid:%s" % self.crawlid, 2 * 24 * 60 * 60)

        print("\ntask feed complete. sucess_rate:%s%%, failed_rate:%s%%" % (success_rate, failed_rate))

    def get_name(self, url):
        return "{sid}:item:queue".format(sid=self.spiderid)

    def feed(self, queue_name, req):
        if self.custom:
            from custom_redis.client.errors import RedisError
        else:
            from redis import RedisError

        try:
            data = json.loads(req)
            if self.meta:
                data.update(self.meta)
            #req = json.dumps(data)
            req = pickle.dumps(data)
            self.redis_conn.zadd(queue_name, req, -self.priority)
            return 0
        except RedisError:
            traceback.print_exc()
            return 1

    def show_process_line(self, count, num, failed):

        per = count / 100
        success = num - failed
        success_rate = success * 100.0 / count
        failed_rate = failed * 100.0 / count
        str_success_rate = "%.2f%%  " % success_rate
        str_failed_rate = "%.2f%%  " % failed_rate

        if num >= self.inc and self.show:
            self.inc += per

            if sys.platform == "win32":
                import ctypes
                std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
                color_ctl = ctypes.windll.kernel32.SetConsoleTextAttribute
                color_ctl(std_out_handle, 2)
                print("\r", str_success_rate, "")
                color_ctl(std_out_handle, 32)
                print(int(success_rate * 30 / 100) * ' ', "")
                if int(failed_rate):
                    color_ctl(std_out_handle, 64)
                    print(int(failed_rate * 30 / 100) * ' ', "")
                color_ctl(std_out_handle, 0)
                color_ctl(std_out_handle, 4)
                print(str_failed_rate, "")
                color_ctl(std_out_handle, 7)
            else:
                print("\r", str_success_rate, "")
                print("%s%s" % (int(success_rate * 50 / 100) * '\033[42m \033[0m',
                                int(failed_rate * 50 / 100) * '\033[41m \033[0m'), str_failed_rate)
        return success_rate, failed_rate

if __name__ == "__main__":

    RF = RedisFeed.parse_args()
    RF.start()