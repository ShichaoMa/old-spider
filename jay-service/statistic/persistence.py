# -*- coding:utf-8 -*-
import pickle
import fnmatch
import datetime
import traceback

from redis import Redis

from .utils import format_title


class RedisStore(object):
    """
    redis db
    """
    def __init__(self, host="192.168.200.90", port=6379):
        self.redis_conn = Redis(host, port)

    def get_datas(self, crawlids=None):
        """
        get records of crawlids
        :param crawlids:
        :return:
        """
        data_lst = []
        if crawlids:
            keys = ["crawlid:%s" % x for x in crawlids]
        else:
            keys = self.redis_conn.keys("crawlid:*")

        pipeline = self.redis_conn.pipeline()
        pipeline.multi()

        for key in keys:
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            if key.count(":") != 1:
                continue
            pipeline.hgetall(key)

        for data in pipeline.execute():
            new_data = format_title(dict((k.decode(), v.decode()) for k, v in data.items()))
            new_data["is_finished"] = self.check_finish(data)
            if not new_data["is_finished"]:
                new_data["miss_pages"] = 0
            data_lst.append(new_data)
        return data_lst

    def destroy(self, crawlid, spiderid):
        """
        destory record which in redis.
        :param crawlid:
        :param spiderid:
        :return:
        """
        self.redis_conn.delete("crawlid:%s"%crawlid)
        if not spiderid:
            spiderid = "*"
        for key in self.redis_conn.scan_iter(match="%s:*:queue"%spiderid):
            try:
                for item in self.redis_conn.zscan_iter(key):
                    item_key = item[0]
                    try:
                        item = pickle.loads(item_key)
                    except Exception:
                        # 在docker中由于没有crawling所以可能会失败
                        continue
                    if 'meta' in item:
                        item = item['meta']

                    if item['crawlid'] == crawlid:
                        self.redis_conn.zrem(key, item_key)
            except Exception:
                traceback.print_exc()

    def get_data(self, crawlid):
        """
        get record of crawlid
        :param crawlid:
        :return:
        """
        datas = self.redis_conn.hgetall(crawlid)
        new_data = dict()
        for key, value in datas.items():
            new_data[key.decode("utf-8")] = value.decode("utf-8")
        return format_title(new_data)

    def get_failed_message(self, crawlid):
        """
        get failed message of crawlid
        :param crawlid:
        :return:
        """
        key = "crawlid:%s" % crawlid
        data = self.redis_conn.hgetall(key)
        failed_keys = [x for x in data.keys() if fnmatch.fnmatch(x, b"failed_download_*")]
        errors = []
        for fk in failed_keys:
            item = {}
            msg = "show the %s. "%fk.decode("utf-8").replace("_", " ")
            item[msg] = [(item[0], item[1].split(b"\n")) for item in self.redis_conn.hgetall(
                "%s:%s"%(fk.decode("utf-8"), crawlid)).items()]
            errors.append(item)
        return errors

    def check_finish(self, data):
        """
        check whether finished of crawlid
        :param crawlid:
        :return:
        """
        total_pages = int(data.get(b"total_pages", 0))
        crawled_pages = int(data.get(b"crawled_pages", 0))
        failed_keys = [x for x in data.keys() if fnmatch.fnmatch(x, b"failed_download_*")]
        failed_pages = 0

        for fk in failed_keys:
            failed_pages += int(data.get(fk, 0))
        if (total_pages <= crawled_pages + failed_pages and total_pages != 0) or (
                        total_pages < crawled_pages + failed_pages and total_pages == 0):
            return True
        now = datetime.datetime.now()
        u_t = data.get(b"update_time", b"").decode()
        update_time = datetime.datetime.strptime(u_t, "%Y-%m-%d %H:%M:%S") if u_t else now
        if (now - update_time).days > 0 or (now - update_time).seconds >= 24*3600 and now > update_time:
            return True