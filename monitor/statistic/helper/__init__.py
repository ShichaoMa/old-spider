# -*- coding:utf-8 -*-
import pickle
import datetime
import traceback

from io import StringIO
from redis import RedisError

from contextlib import contextmanager


TITLE = [
    "crawlid", "spiderid", "start_time", "update_time", "total_minutes",
    "total_pages", "crawled_pages", "failed_download_pages", "crawl_per_minute",
    "success_rate", "miss_pages", "type", "priority"
]


def time_parse(x):
    return datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")


def get_minutes(timedelta):
    days = timedelta.days
    seconds = timedelta.seconds
    return days*24*60+seconds/60.0


def sum(d):
    sum =  0
    for k in d.keys():
        if k.startswith("failed_download"):
            sum += int(d.get(k, 0))
    return sum


FORMAT_FUNC = {
    "failed_download_pages":sum,
    "total_minutes":lambda d:"%.2f"%get_minutes(time_parse(d.get("update_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))-time_parse(d.get("start_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))),
    "crawl_per_minute":lambda d:"%.2f"%(int(d.get("crawled_pages", 0))/float(d.get("total_minutes", 0))),
    "success_rate":lambda d:"%.2f%%"%((100.0*int(d.get("crawled_pages", 0))/int(d.get("total_pages", 0)))),
    "miss_pages":lambda d:int(d.get("total_pages", 0))-int(d.get("crawled_pages", 0))-int(d.get("failed_download_pages", 0))-int(d.get("drop_pages", 0)),
 }


def format_title(task):
    for k in TITLE:
        function = FORMAT_FUNC.get(k)
        if function:
            try:
                task[k] = function(task)
            except Exception:
                task[k] = 0
    return task


def format(d, f=False):
    for k, v in d.items():
        if f:
            print("reason --> %s"%v.ljust(30))
            print("url    --> %s"%k.ljust(30))
        else:
            print("%s -->  %s"%(k.ljust(30), v))


def feed(db, meta, crawlid, priority, url, spiderid, callback):
    queue_name, req = enrich(meta, crawlid, priority, url, spiderid, callback)
    try:
        db.redis_conn.zadd(queue_name, pickle.dumps(req), -priority)
        return 0
    except RedisError:
        traceback.print_exc()
        return 1


def enrich(meta, crawlid, priority, url, spiderid, callback):
    data = {"url": url.strip(),
            "crawlid": crawlid,
            "spiderid": spiderid,
            "callback": callback,
            "priority": priority}
    data.update(meta)
    return "{sid}:item:queue".format(sid=spiderid), data


@contextmanager
def filebuf(fileobj):
    try:
        if isinstance(fileobj, bytes):
            fileobj = fileobj.strip(b"\357\273\277\r\n").decode("utf-8")
        yield StringIO(fileobj)
    finally:
        pass


def ftime(strtime):
    return datetime.datetime.strptime(strtime, "%Y-%m-%d %H:%M:%S")


def _cmp(x, y):
    if ftime(x.get("update_time", "1970-01-01 00:00:00")) > ftime(y.get("update_time", "1970-01-01 00:00:00")):
        return -1
    else:
        return 1


def _key(x):
    return x.get("update_time", "1970-01-01 00:00:00")

