# -*- coding:utf-8 -*-
import os
import io
import re
import sys
import copy
import time
import json
import errno
import types
import socket
import struct
import psutil
import signal
import logging
import datetime
import requests
import traceback

from queue import Empty
from logging import handlers
from collections import OrderedDict
from functools import wraps, reduce
from pythonjsonlogger.jsonlogger import JsonFormatter
from urllib.parse import urlparse, urlunparse, urlencode, urljoin

from scrapy import Selector, Item
from scrapy.loader import ItemLoader
from scrapy.utils.misc import arg_to_iter
from scrapy.loader.processors import Compose, MapCompose


def is_debug():
    return eval(os.environ.get("DEBUG", "False"))


class TakeAll(object):
    """
    自定义TakeAll
    """
    def __call__(self, values):
        return values


class TakeFirst(object):
    """
    自定义TakeFirst
    """
    def __call__(self, values):
        return_value = None
        for value in values:
            return_value = value
            if value:
                return return_value
        return return_value


def duplicate(iterable, key=lambda x: x):
    """
    保序去重
    :param iterable:
    :param key:
    :return:
    """
    result = list()
    for i in iterable:
        keep = key(i)
        if keep not in result:
            result.append(keep)
    return result


def strip(value, chars=None):
    """
    strip字段
    :param value:
    :param chars:
    :return:
    """
    if isinstance(value, str):
        return value.strip(chars)
    return value


def decode(value, encoding="utf-8"):
    """
    decode字段
    :param value:
    :param encoding:
    :return:
    """
    return value.decode(encoding)


def encode(value, encoding="utf-8"):
    """
    encode字段
    :param value:
    :param encoding:
    :return:
    """
    return value.encode(encoding)


def rid(value, old, new):
    """
    去掉指定字段
    :param value:
    :param old:
    :param new:
    :return:
    """
    return value.replace(old, new)


def xpath_exchange(x):
    """
    将xpath结果集进行抽取拼接成字符串
    :param x:
    :return:
    """
    return "".join(x.extract()).strip()


def re_exchange(x):
    """
    将re的结果集进行抽取拼接成字符串
    :param x:
    :param item:
    :return:
    """
    return "".join(x).strip()


def wrap_key(json_str, key_pattern=re.compile(r"([a-zA-Z_]\w*)[\s]*\:")):
    """
    将javascript 对象字串串形式的key转换成被双字符包裹的格式如{a: 1} => {"a": 1}
    :param json_str:
    :param key_pattern:
    :return:
    """
    json_str = key_pattern.sub('"\g<1>":', json_str)
    return json_str


def safely_json_loads(json_str, defaulttype=dict, escape=True):
    """
    返回安全的json类型
    :param json_str: 要被loads的字符串
    :param defaulttype: 若load失败希望得到的对象类型
    :param escape: 是否将单引号变成双引号
    :return:
    """
    if not json_str:
        return defaulttype()
    elif escape:
        data = replace_quote(json_str)
        return json.loads(data)
    else:
        return json.loads(json_str)


def chain_all(iter):
    """
    连接两个序列或字典
    :param iter:
    :return:
    """
    iter = list(iter)
    if not iter:
        return []
    if isinstance(iter[0], dict):
        result = {}
        for i in iter:
            result.update(i)
    else:
        result = reduce(lambda x, y: list(x)+list(y), iter)
    return result


def replace_quote(json_str):
    """
    将要被json.loads的字符串的单引号转换成双引号，如果该单引号是元素主体，而不是用来修饰字符串的。则不对其进行操作。
    :param json_str:
    :return:
    """
    if not isinstance(json_str, str):
        return json_str
    double_quote = []
    new_lst = []
    for index, val in enumerate(json_str):
        if val == '"' and json_str[index-1] != "\\":
            if double_quote:
                double_quote.pop(0)
            else:
                double_quote.append(val)
        if val== "'" and json_str[index-1] != "\\":
            if not double_quote:
                val = '"'
        new_lst.append(val)
    return "".join(new_lst)


def format_html_string(html):
    """
    格式化html
    :param html:
    :return:
    """
    trims = [(r'\n',''),
             (r'\t', ''),
             (r'\r', ''),
             (r'  ', ''),
             (r'\u2018', "'"),
             (r'\u2019', "'"),
             (r'\ufeff', ''),
             (r'\u2022', ":"),
             (r"<([a-z][a-z0-9]*)\ [^>]*>", '<\g<1>>'),
             (r'<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', ''),
             (r"</?a.*?>", '')]
    return reduce(lambda string, replacement: re.sub(*replacement, string), trims, html)


def urldecode(query):
    """
    与urlencode相反，不过没有unquote
    :param query:
    :return:
    """
    if not query.strip():
        return dict()
    return dict(x.split("=") for x in query.strip().split("&"))


def re_search(re_str, text, dotall=True):
    """
    抽取正则规则的第一组元素
    :param re_str:
    :param text:
    :param dotall:
    :return:
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    if not isinstance(re_str, list):
        re_str = [re_str]

    for rex in re_str:
        if isinstance(rex, str):
            rex = re.compile(rex)
        if dotall:
            match_obj = rex.search(text, re.DOTALL)
        else:
            match_obj = rex.search(text)

        if match_obj is not None:
            t = match_obj.group(1).replace('\n', '')
            return t

    return ""


def retry_wrapper(retry_times, exception=Exception, error_handler=None, interval=0.1):
    """
    函数重试装饰器
    :param retry_times: 重试次数
    :param exception: 需要重试的异常
    :param error_handler: 出错时的回调函数
    :param interval: 重试间隔时间
    :return:
    """
    def out_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    count += 1
                    if error_handler:
                        result = error_handler(func.__name__, count, e, *args, **kwargs)
                        if result:
                            count -= 1
                    if count >= retry_times:
                        raise
                    time.sleep(interval)
        return wrapper

    return out_wrapper


class P22P3Encoder(json.JSONEncoder):
    """
    python2转换python3时使用的json encoder
    """
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        if isinstance(obj, (types.GeneratorType, map, filter)):
            return list(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class ItemEncoder(json.JSONEncoder):
    """
    将Item转换成字典
    """
    def default(self, obj):
        if isinstance(obj, Item):
            return dict(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def timeout(timeout_time, default):
    """
    Decorate a method so it is required to execute in a given time period,
    or return a default value.
    :param timeout_time:
    :param default:
    :return:
    """
    class DecoratorTimeout(Exception):
        pass

    def timeout_function(f):
        def f2(*args):
            def timeout_handler(signum, frame):
                raise DecoratorTimeout()

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            # triger alarm in timeout_time seconds
            signal.alarm(timeout_time)
            try:
                retval = f(*args)
            except DecoratorTimeout:
                return default
            finally:
                signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)
            return retval

        return f2

    return timeout_function


def custom_re(regex, text):
    """
    模仿selector.re
    :param regex:
    :param text:
    :return:
    """
    return re.findall(regex, text)


def replace_dot(data):
    """
    mongodb不支持key中带有.，该函数用来将.转换成_
    :param data:
    :return:
    """
    new_data = {}
    for k, v in data.items():
        new_data[k.replace(".", "_")] = v

    return new_data


def groupby(it, key):
    """
    自实现groupby，itertool的groupby不能合并不连续但是相同的组, 且返回值是iter
    :return: 字典对象
    """
    groups = dict()
    for item in it:
        groups.setdefault(key(item), []).append(item)
    return groups


class CustomLoader(ItemLoader):
    """
    自定义ItemLoader
    """
    default_output_processor = Compose(MapCompose(strip), TakeFirst())

    def add_re(self, field_name, regex, **kwargs):
        """
        自实现add_re方法
        :param field_name:
        :param regex:
        :param kwargs:
        :return:
        """
        replace_entities = True
        regexs = arg_to_iter(regex)
        while True:
            try:
                for regex in regexs:
                    self.add_value(field_name, self.selector.re(regex, replace_entities), **kwargs)
                break
            except json.decoder.JSONDecodeError:
                replace_entities = False

    def load_item(self):
        """
        增加skip, default, order的实现
        :return:
        """
        item = self.item
        skip_fields = []
        for field_name, field in sorted(item.fields.items(), key=lambda item: item[1].get("order", 0)):
            value = self.get_output_value(field_name)
            if field.get("skip"):
                skip_fields.append(field_name)
            item[field_name] = value or field.get("default", "")

        for field in skip_fields:
            del item[field]
        return item

    def __str__(self):
        return "<CustomLoader item: %s at %s >" % (self.item.__class__, id(self))

    __repr__ = __str__


def enrich_wrapper(func):
    """
    item_loader在使用pickle 序列化时，不能包含response对象和selector对象, 使用该装饰器，
    在进去enrich函数之前加上selector，使用完毕后清除selector
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        item_loader = args[1]
        response = args[2]
        selector = Selector(text=response.text)
        item_loader.selector = selector
        result = func(*args, **kwargs)
        item_loader.selector = None

        return result

    return wrapper


def parse_cookie(string):
    """
    解析cookie
    :param string:
    :return:
    """
    results = re.findall('([^=]+)=([^\;]+);?\s?', string)
    my_dict = {}

    for item in results:
        my_dict[item[0]] = item[1]

    return my_dict


def _get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    import fcntl
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(), 0x8915, struct.pack('256s', ifname[:15])
    )[20:24])


def _get_net_interface():

    p = os.popen("ls /sys/class/net")
    buf = p.read(10000)
    return buf.strip(" \nlo")


def get_netcard():
    netcard_info = []
    info = psutil.net_if_addrs()
    for k,v in info.items():
        for item in v:
            if item[0] == 2 and not item[1]=='127.0.0.1':
                netcard_info.append((k,item[1]))
    return netcard_info


def get_ip_address():
    """
    获取本机局域网ip
    :return:
    """
    if sys.platform == "win32":
        hostname = socket.gethostname()
        IPinfo = socket.gethostbyname_ex(hostname)
        try:
            return IPinfo[-1][-1]
        except IndexError:
            return "127.0.0.1"
    else:
        ips = get_netcard()

        if ips:
            return ips[0][1]
        else:
            shell_command = "ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/'"
            return os.popen(shell_command).read().strip()


def url_arg_increment(arg_pattern, url):
    """
    对于使用url arguments标志page字段而实现分页的url，使用这个函数生成下一页url
    关于正则表达式：
    第一组匹配url分页参数前面的部分
    第二组匹配分页参数的名字+等号+起始页的页序数
    第三组匹配当前页数
    第四组匹配分页参数后来的值
    正常使用时，一 三 四组不需要修改，只需要修改第二组中的值即可
    @param arg_pattern:r'(.*?)(pn=0)(\d+)(.*)',
    @param url:http://www.nike.com/abc?pn=1
    @return:http://www.nike.com/abc?pn=2
    """
    first_next_page_index = int(re.search(r"\d+", arg_pattern).group())
    arg_pattern = arg_pattern.replace(str(first_next_page_index), "")
    mth = re.search(arg_pattern, url)
    if mth:
        prefix = mth.group(1)
        midfix = mth.group(2)
        page = int(mth.group(3))
        stuffix = mth.group(4)
        return "%s%s%s%s" % (prefix, midfix, page + 1, stuffix)
    else:
        midfix = re.sub(r"[\(\)\\d\+\.\*\?]+", "", arg_pattern)
        if url.count("?"):
            midfix = "&" + midfix
        else:
            midfix = "?" + midfix
        return "%s%s%s" % (url, midfix, first_next_page_index + 1)


def url_item_arg_increment(partten, url, count):
    """
    对于使用url arguments标志item的partten而实现分页的url，使用这个函数生成下一页url
    @param partten: `keyword`=`begin_num`(eg: start=0)用来指定partten的相应字段
    @param url: http://www.ecco.com/abc?start=30
    @param count:  30当前页item的数量
    @return: http://www.ecco.com/abc?start=60
    """
    keyword, begin_num = partten.split("=")
    mth = re.search(r"%s=(\d+)"%keyword, url)
    if mth:
        start = int(mth.group(1))
    else:
        start = int(begin_num)
    parts = urlparse(url)
    if parts.query:
        query = dict(x.split("=") for x in parts.query.split("&"))
        query[keyword] = start + count
    else:
        query = {keyword: count+1}
    return urlunparse(parts._replace(query=urlencode(query)))


def url_path_arg_increment(pattern_str, url):
    """
    对于将页数放到path中的url,使用这个函数生成下一页url
    如下：
    其中{first_page_num}~={regex}用来标明该url是用urlpath中某一部分自增来进行翻页
    ~=前面代表该分类第一页若是缺省页面，是从第几页开始计算
    ~=后面为正则表达式
        第一组用来匹配自增数字前面可能存在的部分（可为空）
        第二组用来匹配自增数字
        第三组来匹配自增数字后面可能存在的部分（可为空）
    如示例中给出的url，经过转换后得到下一页的url为
    'http://www.timberland.com.hk/en/men-apparel-shirts/page/2/'
    其中http://www.timberland.com.hk/en/men-apparel-shirts为原url
    /page/为第一组所匹配; 2为第二组匹配的; /为第三组匹配的
    当给出的url为'http://www.timberland.com.hk/en/men-apparel-shirts/page/2/'
    输出结果为'http://www.timberland.com.hk/en/men-apparel-shirts/page/3/'
    @param pattern_str: r'1~=(/page/)(\d+)(/)'
    @param url: 'http://www.timberland.com.hk/en/men-apparel-shirts‘
    @return:'http://www.timberland.com.hk/en/men-apparel-shirts/page/2/'
    """
    parts = urlparse(url)
    first_page_num, pattern = pattern_str.split("~=", 1)
    mth = re.search(pattern, parts.path)
    if mth:
        path = re.sub(pattern, "\g<1>%s\g<3>"%(int(mth.group(2))+1), parts.path)
    else:
        page_num = int(first_page_num) + 1
        path = re.sub(r"\((.*)\)(?:\(.*\))\((.*)\)", _repl_wrapper(parts.path, page_num), pattern).replace("\\", "")
    return urlunparse(parts._replace(path=path))


def _repl_wrapper(path, page_num):

    def _repl(mth):
        sub_path = "%s%d%s"%(mth.group(1), page_num, mth.group(2))
        if path.endswith(mth.group(2).replace("\\", "")):
            return path[:path.rfind(mth.group(2).replace("\\", ""))]+sub_path
        else:
            return path + sub_path

    return _repl


class ItemCollectorPath(object):
    """
        ItemCollector路径类
    """
    def __init__(self, raw='/'):
        self.datum = []
        if not raw.startswith('/'):
            raise Exception("Not valid string found: %s" % str)

        if '/' == raw:
            self.datum.append('')
        else:
            self.datum = list(map(lambda x: tuple(x.split('#', 1)) if '#' in x else x, raw.split('/')))

    def depth(self):
        return len(self.datum)

    def is_empty(self):
        return self.depth() == 1

    def is_root(self):
        return self.is_empty()

    def add(self, part, pos=None):
        if pos is None:
            self.datum.append(part)
        else:
            self.datum.append((part, pos))

    def pop(self):
        if self.is_empty():
            raise Exception("Empty, can't pop.")

        return self.datum.pop()

    def last_part(self):
        x = self.datum[-1]
        if isinstance(x, tuple):
            return "%s#%s" % (x[0], x[1])
        else:
            return str(x)

    def last_prop(self):
        return self.last_part().split('#', 1)[0]

    def parent(self):
        s = str(self)
        t = ItemCollectorPath(s)
        t.pop()
        return t

    def __le__(self, other):
        return len(self.datum) <= len(self.datum)

    def __ge__(self, other):
        return len(self.datum) >= len(self.datum)

    def __lt__(self, other):
        return len(self.datum) < len(self.datum)

    def __gt__(self, other):
        return len(self.datum) > len(self.datum)

    def __str__(self):
        if 1 == len(self.datum):
            return '/'
        else:
            return '/'.join(map(
                lambda x: "%s#%s" % (x[0], x[1]) if isinstance(x, tuple) else str(x), self.datum
            ))

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class ItemCollector(object):
    """
    ItemCollector的实现
    """
    def __init__(self):
        self.item_loaders = {}
        self.request_hashs = []

    def add_request(self, request):
        self.request_hashs.append(request)

    def add_requests(self, requests):
        self.request_hashs.extend(requests)

    def have_request(self):
        return len(self.request_hashs) != 0

    def pop_request(self):
        return self.request_hashs.pop()

    def add_item_loader(self, path, item_loader):
        self.item_loaders[path] = item_loader

    def item_loader(self, path):
        return self.item_loaders[path]

    def parent_item_loader(self, path):
        return self.item_loaders[path.parent()]

    def load_item(self):
        entries = sorted(self.item_loaders.items(), key=lambda x: x[0])
        while len(entries) > 0:
            path, item_loader = entries.pop()

            if not (path == '/'):
                if self.parent_item_loader(path) != item_loader:
                    self.parent_item_loader(path).add_value(
                        path.last_prop(), item_loader.load_item()
                    )
            else:
                break

        return item_loader.load_item()


def async_produce_wrapper(producer, logger):
    """
    pykafka实现异步生产时，使用的装饰器
    :param producer:
    :param logger:
    :return:
    """
    count = 0

    def wrapper(func):

        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            nonlocal count
            count += 1
            if count % 10 == 0:  # adjust this or bring lots of RAM ;)
                while True:
                    try:
                        msg, exc = producer.get_delivery_report(block=False)
                        if exc is not None:
                            logger.error('Failed to deliver msg {}: {}'.format(
                                msg.partition_key, repr(exc)))
                        else:
                            logger.info('Successfully delivered msg {}'.format(
                                msg.partition_key))
                    except Empty:
                        break
            return result
        return inner
    return wrapper


def post_es(host, port, fingerprint):
    """
    查找该fingerprint在es中是否存在
    :param host:
    :param port:
    :param fingerprint:
    :return:
    """
    resp = requests.post(url="http://%s:%s/roc/parent_ware/_search"%(host, port), json={
        "query": {
            "term": {
                "fingerprint": fingerprint
            }
        }
    })
    if json.loads(resp.text)["hits"]["total"]:
        return True


def re_size(x, y):
    """
    eastbay缩小图片专用
    :param x:
    :param y:
    :return:
    """
    x, y = int(x), int(y)
    m = max(x, y)
    if m > 2000:
        if m == x:
            y, x = y * 2000 // x, 2000
        else:
            x, y = x * 2000 // y, 2000
    return x, y


def extras_wrapper(self, item):
    """
    logger的extra转用装饰器
    :param self:
    :param item:
    :return:
    """
    def logger_func_wrapper(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 2:
                extras = args[1]
            else:
                extras = kwargs.pop("extras", {})
            extras = self.add_extras(extras, item)
            return func(args[0], extra=extras)

        return wrapper

    return logger_func_wrapper


def findCaller(stack_info=False):
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    f = logging.currentframe()
    #On some versions of IronPython, currentframe() returns None if
    #IronPython isn't run with -X:Frames.
    if f is not None:
        f = f.f_back
    rv = "(unknown file)", 0, "(unknown function)", None
    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if not (filename.count("crawling") and not filename.count("utils")):
            f = f.f_back
            continue
        sinfo = None
        if stack_info:
            sio = io.StringIO()
            sio.write('Stack (most recent call last):\n')
            traceback.print_stack(f, file=sio)
            sinfo = sio.getvalue()
            if sinfo[-1] == '\n':
                sinfo = sinfo[:-1]
            sio.close()
        rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
        break
    return rv


def logger_find_call_wrapper(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        return findCaller(*args, **kwargs)
    return wrapper


class CustomJsonFormatter(JsonFormatter):

    def format(self, record):
        """Formats a log record and serializes to json"""
        message_dict = {}
        if isinstance(record.msg, dict):
            message_dict = record.msg
            record.message = None
        else:
            record.message = record.getMessage()
        # only format time if needed
        if "asctime" in self._required_fields:
            record.asctime = self.formatTime(record, self.datefmt)

        # Display formatted exception, but allow overriding it in the
        # user-supplied dict.
        if record.exc_info and not message_dict.get('exc_info'):
            message_dict['exc_info'] = self.formatException(record.exc_info)
        if not message_dict.get('exc_info') and record.exc_text:
            message_dict['exc_info'] = record.exc_text
        message_dict["module"] = record.module
        message_dict["lineno"] = record.lineno
        message_dict["funcName"] = record.funcName

        try:
            log_record = OrderedDict()
        except NameError:
            log_record = {}
        self.add_fields(log_record, record, message_dict)
        log_record = self.process_log_record(log_record)

        return "%s%s" % (self.prefix, self.jsonify_log_record(log_record))


class UDPLogstashHandler(handlers.DatagramHandler):
    """Python logging handler for Logstash. Sends events over UDP.
    :param host: The host of the logstash server.
    :param port: The port of the logstash server (default 5959).
    :param message_type: The type of the message (default logstash).
    :param fqdn; Indicates whether to show fully qualified domain name or not (default False).
    :param version: version of logstash event schema (default is 0).
    :param tags: list of tags for a logger (default is None).
    """

    def makePickle(self, record):
        return self.formatter.format(record).encode("utf-8")


class Logger(object):
    """
    logger的实现
    """
    logger = None

    def __new__(cls, *args, **kwargs):
        # 保证单例
        if not cls.logger:
            cls.logger = super(Logger, cls).__new__(cls)
        return cls.logger

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.findCaller = logger_find_call_wrapper(self.logger.findCaller)

    @classmethod
    def from_crawler(cls, crawler):
        return Logger.logger or cls.init_logger(crawler)

    @classmethod
    def init_logger(cls, crawler):
        return cls.from_settings(crawler.settings, crawler.spidercls.name)

    @classmethod
    def from_settings(cls, settings, name):
        json = settings.get('SC_LOG_JSON', True)
        level = settings.get('SC_LOG_LEVEL', 'INFO')
        name = "%s_%s" % (name, get_ip_address().replace(".", "_"))
        stdout = settings.get('SC_LOG_STDOUT', True)
        # dir = settings.get('LOG_DIR', 'logs')
        # bytes = settings.get('LOG_MAX_BYTES', '10MB')
        # backups = settings.get('LOG_BACKUPS', 5)
        udp_host = settings.get("SC_LOG_UDP_HOST", "192.168.200.132")
        udp_port = settings.getint("SC_LOG_UDP_PORT", 5230)
        logger = cls(name=name)
        logger.logger.propagate = False
        logger.json = json
        logger.name = name
        logger.format_string = '%(asctime)s [%(name)s]%(levelname)s: %(message)s'
        root = logging.getLogger()
        # 将的所有使用Logger模块生成的logger设置一样的logger level
        for log in root.manager.loggerDict.keys():
            root.getChild(log).setLevel(getattr(logging, level, 10))

        if stdout:
            logger.set_handler(logging.StreamHandler(sys.stdout))
        else:
            # try:
            #     os.makedirs(dir)
            # except OSError as exception:
            #     if exception.errno != errno.EEXIST:
            #         raise
            #
            # file_handler = handlers.RotatingFileHandler(
            #     os.path.join(dir, file),
            #     maxBytes=bytes,
            #     backupCount=backups)
            # logger.set_handler(file_handler)
            logger.set_handler(UDPLogstashHandler(udp_host, udp_port))
        return logger

    def set_handler(self, handler):
        handler.setLevel(logging.DEBUG)
        formatter = self._get_formatter(self.json)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.debug("Logging to %s"%handler.__class__.__name__)

    def __getattr__(self, item):
        if item.upper() in logging._nameToLevel:
            return extras_wrapper(self, item)(getattr(self.logger, item))
        raise AttributeError

    def _get_formatter(self, json):
        if json:
            return CustomJsonFormatter()
        else:
            return logging.Formatter(self.format_string)

    def add_extras(self, dict, level):
        my_copy = copy.deepcopy(dict)
        if 'level' not in my_copy:
            my_copy['level'] = level
        if 'timestamp' not in my_copy:
            my_copy['timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if 'logger' not in my_copy:
            my_copy['logger'] = self.name
        return my_copy


class LoggerDescriptor(object):
    """
    logger描述符，用来懒加载logger
    """
    def __init__(self, logger=None):
        self.logger = logger

    def __get__(self, instance, cls):
        if not self.logger:
            self.logger = Logger.from_crawler(instance.crawler)

        return self.logger

    def __getattr__(self, item):
        raise AttributeError


def get_val(sel_meta, response, item=None, is_after=False, self=None, key=None):
    """
    早期版本，仅在amazon captcha时还有使用
    :param sel_meta:
    :param response:
    :param item:
    :param is_after:
    :param self:
    :param key:
    :return:
    """
    sel = response.selector if hasattr(response, "selector") else response
    value = ""
    expression_list = ["re", "xpath", "css"]
    while not value:

        try:
            selector = expression_list.pop(0)
        except IndexError:
            break
        expressions = sel_meta.get(selector)

        if expressions:
            function = sel_meta.get("function") or globals()["function_%s_common" % selector]

            if is_after:
                function = sel_meta.get("function_after") or function

            for expression in expressions:
                try:
                    raw_data = getattr(sel, selector)(expression)
                    try:
                        value = function(raw_data, item)
                    except Exception:
                        if sel_meta.get("catch", False):
                            value = None
                        else:
                            raise
                except Exception as ex:
                    if self.crawler.settings.get("PDB_DEBUG", False):
                        traceback.print_exc()
                        import pdb
                        pdb.set_trace()
                    if ex:
                        raise
                if value:
                    break

    if not value:
        try:
            extract = sel_meta.get("extract")
            if is_after:
                extract = sel_meta.get("extract_after") or extract
            if extract:
                value = extract(item, response)
        except Exception as ex:
            if self.crawler.settings.get("PDB_DEBUG", False):
                traceback.print_exc()
                import pdb
                pdb.set_trace()
            if ex:
                raise

    return value


def get_from_other_site(url, scrapy_process_url, spiderid):
    data = {
        "urls": [url],
        "spiderid": spiderid
    }
    body = None
    try:
        body = requests.get(scrapy_process_url, json=data, timeout=30).text
        return json.loads(body)
    except Exception as e:
        return {"error": str(e), "url": url, "body": body}


def use_curl(url, proxy=None, proxy_auth=None):
    cmd = """curl -o - -s -w "%%{http_code}\n" '%s' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.8,en;q=0.6' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' --compressed"""%url
    print(cmd)
    if proxy:
        cmd += " -x '%s'"%proxy
        if proxy_auth:
            cmd += " -U '%s'"%proxy_auth
    return os.popen(cmd).readlines()


def drugstore_image_urls(full_image_url, image_urls):

    while 1:
        response_image = requests.get(full_image_url)
        sel = Selector(text=response_image.text)
        image_url = ''.join(sel.xpath('//*[@id="productImage"]/img/@src'))
        image_urls.append(image_url)
        no_next_image = sel.xpath('//img[contains(@src,"right_arrow_grey.gif") and @alt="no image"]')

        if no_next_image:
            break
        else:
            full_image_url = urljoin(
                full_image_url,
                ''.join(sel.xpath('//img[@alt="see next image"]/../@href'))
            )
            if not full_image_url:
                break
    return image_urls


def asos_get_skus(response):
    product_lists=[]
    size_list = re.findall(r'Array\((.*?,"\S*?",".*?",".*?",.*?)\);', response.body)

    for i in size_list:
        pro_dict = []
        size_list = [x.strip('"').strip("'") for x in i.split(',')]
        pro_dict.append(size_list)
        pattern = re.compile(r'"' + size_list[0] + size_list[2] +'":(\{.*?\})')
        sku_dict = json.loads(re.search(pattern, response.body).group(1))
        pro_dict.append(sku_dict)
        product_lists.append(pro_dict)

    return product_lists


def ae_get_colors(response):
    products_list = []
    pd_jsons = re.findall(r'\S*?\:\{colorId.*?sizedd:\[(.*?)\],(colorName:.*?,colorPrdId:.*?),.*?Information:.*?\}',
                          ''.join(re.findall(r'pdpJson:(\{.*?\})\}.*?\};', response.body)))

    for color_tuple in pd_jsons:
        prolist = []
        color_str = ''.join(color_tuple)
        size_list = re.findall(r'\{(.*?)\}', color_str)
        color_list = re.findall(r'(colorName:.*?,colorPrdId:.*)', color_str)
        for size_str in size_list:
            prolist.append(dict([[x.strip('"').strip("'") for x in l.split(':')] for l in size_str.split(',')]))

        for color in color_list:
            prolist.append(dict([[x.strip('"').strip("'") for x in l.split(':')] for l in color.split(',')]))
        products_list.append(prolist)
    return products_list


def shoebug_image_urls(response):
    prefix = ''.join(re.findall(r'"mcfileroot":"(.*?)"', response.body))
    color_dict = [json.loads(x) for x in re.findall(
        r'\{.*?\}', ''.join(re.findall(r'"colors":\[(\{.*?\})+\],', response.body)))]
    image_urls = []

    for color in color_dict:
        color_id = color['id']
        image_urls.extend(
            'http://www.shoebuy.com' + prefix + str(color_id) + '_jb' + str(x) + '.jpg' for x in color['multiImages'])

    return image_urls


def bloomingdales_price_size(response):
    price_size = []
    price_list = [','.join(x).replace('"','') for x in re.findall(
        r'"id":.*?,("upc":.*?),.*?"price":\{('
        r'"originalPrice":.*?,"intermediatePrice":.*?,"retailPrice":.*?),.*?\}', response.body)]

    for i in price_list:
        price_size.append(dict(tuple(x.split(':')) for x in i.split(',')))

    return price_size


def bloomingdales_color_map(response):

    primary = json.loads(''.join(re.findall(r'BLOOMIES.pdp.primaryImages\[.*?\].*?=.*?(\{.*?\})', response.body)))
    additional = json.loads(''.join(re.findall(r'BLOOMIES.pdp.additionalImages\[.*?\].*?=.*?(\{.*?\})', response.body)))
    for k1, v1 in primary.items():
        for k2, v2 in additional.items():
            if k1 == k2:
                primary[k1] = primary[k1] + ',' + additional[k2]

    return primary

def bloomingdales_image_urls(response):

    image_urls = []
    image_url_dicts = bloomingdales_color_map(response)

    for i in image_url_dicts.values():
        for rel_url in i.split(','):
            url = "http://images.bloomingdales.com/is/image/BLM/products/%s?" \
                  "wid=1424&qlt=90,0&layer=comp&op_sharpen=0&resMode=sharp2&op_usm=0.7,1.0,0.5,0&fmt=jpeg" % rel_url
            image_urls.append(url)

    return list(set(image_urls))


def joesnewbalanceoutlet_image_urls(x, item):

    product_id = item["product_id"]
    image_urls = []
    for code in x.extract():
        id = re.search(r"AltView\('(\d+?)', '(\w+?)'", code).group(1)
        prefix, stuffix = ("", "xl") if id == "0" else ('alt_views/', "alt%s"%id)
        image_urls.append(urljoin(item["response_url"], "/products/%s%s_%s.jpg"%(prefix, product_id, stuffix)))
    return image_urls


def neimanmarcus_color_size(item, response):

    size_and_color_json_obj = safely_json_loads(response.body)
    size_color = []
    sku_str = ''.join(size_and_color_json_obj['ProductSizeAndColor']['productSizeAndColorJSON'])
    for sku in re.findall(r'"skus":\[(.*?)\]', sku_str):
        for per_sku in re.findall(r'(\{.*?\})', sku):
            size_color.append(safely_json_loads(per_sku))
    return size_color


if __name__ == "__main__":
    print(url_path_arg_increment(r"0~=(/)(\d+)()", 'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-men-c-jewelry-watches-watches-men'))
