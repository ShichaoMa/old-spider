# -*- coding:utf-8 -*-
import os
import io
import re
import sys
import json
import logging
import requests
import traceback

from functools import wraps
from logging import handlers
from collections import OrderedDict
from pythonjsonlogger.jsonlogger import JsonFormatter
from urllib.parse import urlparse, urlunparse, urlencode

from scrapy import Selector, Item
from scrapy.loader import ItemLoader
from scrapy.utils.misc import arg_to_iter
from scrapy.loader.processors import Compose, MapCompose

from toolkit import get_ip, strip
from toolkit.logger import UDPLogstashHandler, Logger


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


class ItemEncoder(json.JSONEncoder):
    """
    将Item转换成字典
    """
    def default(self, obj):
        if isinstance(obj, Item):
            return dict(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


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
        regexs = arg_to_iter(regex)
        for regex in regexs:
            try:
                self.add_value(field_name, self.selector.re(regex), **kwargs)
            except json.decoder.JSONDecodeError:
                self.add_value(field_name, self.selector.re(regex, False), **kwargs)

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
            if not (value or isinstance(value, type(field.get("default", "")))):
                item[field_name] = field.get("default", "")
            else:
                item[field_name] = value

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


def extract_specs(sel, xpath, child_xpath="th//text()|td//text()"):
    specs = []
    for tr in sel.xpath(xpath):
        k_v = tr.xpath(child_xpath).extract()
        if len(k_v) == 2 and [i for i in k_v if i.strip()]:
            specs.append(k_v)
    return specs


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


class CustomLogger(Logger):
    """
    logger的实现
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler.spidercls.name)

    def __init__(self, settings, name):
        self.json = settings.getbool('SC_LOG_JSON', True)
        self.level = settings.get('SC_LOG_LEVEL', 'DEBUG')
        self.stdout = settings.getbool('SC_LOG_STDOUT', True)
        self.dir = settings.get('SC_LOG_DIR', 'logs')
        self.bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        self.backups = settings.getint('SC_LOG_BACKUPS', 5)
        self.udp_host = settings.get("SC_LOG_UDP_HOST", "127.0.0.1")
        self.udp_port = settings.getint("SC_LOG_UDP_PORT", 5230)
        self.log_file = settings.getbool('SC_LOG_FILE', False)
        self.name = "%s_%s" % (name, get_ip())
        self.logger = logging.getLogger(self.name)
        self.logger.propagate = False
        self.set_up()


class LoggerDescriptor(object):
    """
    logger描述符，用来懒加载logger
    """
    def __init__(self, logger=None):
        self.logger = logger

    def __get__(self, instance, cls):
        if not self.logger:
            self.logger = CustomLogger.from_crawler(instance.crawler)

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


if __name__ == "__main__":
    print(url_path_arg_increment(r"0~=(/)(\d+)()", 'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-men-c-jewelry-watches-watches-men'))
