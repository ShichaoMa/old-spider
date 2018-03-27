import datetime

from functools import wraps


TITLE = [
    "crawlid", "spiderid", "start_time", "update_time", "total_minutes",
    "total_pages", "crawled_pages", "failed_download_pages", "crawl_per_minute",
    "success_rate", "miss_pages", "type", "priority"
]


def sum(d):
    sum = 0
    for k in d.keys():
        if k.startswith("failed_download"):
            sum += int(d.get(k, 0))
    return sum


FORMAT_FUNC = {
    "failed_download_pages": sum,
    "total_minutes":lambda d:"%.2f"%get_minutes(
        time_parse(d.get("update_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))-
        time_parse(d.get("start_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))),
    "crawl_per_minute":lambda d:"%.2f"%(int(d.get("crawled_pages", 0))/float(d.get("total_minutes", 0))),
    "success_rate":lambda d:"%.2f%%"%((100.0*int(d.get("crawled_pages", 0))/int(d.get("total_pages", 0)))),
    "miss_pages":lambda d:int(d.get("total_pages", 0))-int(d.get("crawled_pages", 0))-
                          int(d.get("failed_download_pages", 0))-int(d.get("drop_pages", 0)),
 }


def routing(**kwargs):
    """
    routing function
    :param kwargs:
    :return:
    """
    def out_wrapper(func):
        func.meta = kwargs
        return func
    return out_wrapper


def time_parse(x):
    return datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")


def get_minutes(timedelta):
    days = timedelta.days
    seconds = timedelta.seconds
    return days*24*60+seconds/60.0


def format_title(task):
    for k in TITLE:
        function = FORMAT_FUNC.get(k)
        if function:
            try:
                task[k] = function(task)
            except Exception:
                task[k] = 0
    return task


def cache_property(func):

    @property
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        prop_name = "_%s"%func.__name__
        if prop_name not in self.__dict__:
            self.__dict__[prop_name] = func(*args, **kwargs)
        return self.__dict__[prop_name]
    return wrapper
