# -*- coding:utf-8 -*-
import re
import os
import glob
import time
import socket
import base64
import random
import traceback

from threading import RLock
from io import StringIO
from http import cookiejar
from collections import defaultdict
from w3lib.url import safe_url_string
from redis.exceptions import WatchError
from urllib.parse import urljoin, urlencode, urlunparse,  urlparse
from urllib.request import build_opener, Request, HTTPCookieProcessor, ProxyHandler

from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from scrapy import Selector, signals
from scrapy.xlib.tx import ResponseFailed
from scrapy.http.cookies import WrappedRequest, WrappedResponse
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

from .spiders.exception_process import process_exception_method_wrapper, \
    process_requset_method_wrapper, process_response_method_wrapper, stats_wrapper
from .spiders.utils import Logger, parse_cookie, \
    get_val, get_ip_address, timeout
from .spiders.captcha_field import CAPTCHA_FIELD
from .custom_cookie_jar import CookieJar


class DownloaderBaseMiddleware(object):
    def __init__(self, settings):
        self.logger = Logger.from_crawler(self.crawler)
        self.settings = settings

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        obj = cls(crawler.settings)
        return obj


class CustomUserAgentMiddleware(UserAgentMiddleware, DownloaderBaseMiddleware):
    def __init__(self, settings, user_agent='Scrapy'):
        DownloaderBaseMiddleware.__init__(self, settings)
        UserAgentMiddleware.__init__(self)
        user_agent_list = settings.get('USER_AGENT_LIST')

        if not user_agent_list:
            ua = settings.get('USER_AGENT', user_agent)
            self.user_agent_list = [ua]
        else:
            self.user_agent_list = [i.strip() for i in user_agent_list.decode("utf-8").split('\n') if i.strip()]

        self.default_agent = user_agent
        self.choicer = self.choice()
        self.user_agent = self.choicer.__next__() or user_agent

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        obj = cls(crawler.settings)
        crawler.signals.connect(obj.spider_opened,
                                signal=signals.spider_opened)
        return obj

    def choice(self):
        while True:
            if self.user_agent_list:
                for user_agent in self.user_agent_list:
                    yield user_agent
            else:
                yield None

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        self.user_agent = self.choicer.__next__() or self.default_agent

        if self.user_agent:
            request.headers['User-Agent'] = self.user_agent
            self.logger.debug('User-Agent: {} {}'.format(request.headers.get('User-Agent'), request))
        else:
            self.logger.error('User-Agent: ERROR with user agent list')


class CustomRedirectMiddleware(DownloaderBaseMiddleware, RedirectMiddleware):
    def __init__(self, settings):
        RedirectMiddleware.__init__(self, settings)
        DownloaderBaseMiddleware.__init__(self, settings)
        self.stats = self.crawler.stats

    @process_response_method_wrapper
    def process_response(self, request, response, spider):

        if request.meta.get('dont_redirect', False):
            return response

        if response.status in [302, 303] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, safe_url_string(response.headers['location']))
            redirected = self._redirect_request_using_get(request, redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        if response.status in [301, 307] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, safe_url_string(response.headers['location']))
            redirected = request.replace(url=redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        return response

    def _redirect(self, redirected, request, spider, reason):

        reason = response_status_message(reason)
        redirects = request.meta.get('redirect_times', 0) + 1

        if redirects <= self.max_redirect_times:
            redirected.meta['redirect_times'] = redirects
            redirected.meta['redirect_urls'] = request.meta.get('redirect_urls', []) + \
                                               [request.url]
            redirected.meta['priority'] = redirected.meta['priority'] + self.priority_adjust
            self.logger.warn("Redirecting %s to %s from %s for %s times " % (
                reason, redirected.url, request.url, redirected.meta.get("redirect_times")))
            return redirected
        else:
            self.logger.warn("Discarding %s: max redirections reached" % request.url)
            # 错误信息记录出错的url ，而不是最初的url
            # request.meta["url"] = request.url

            if request.meta.get("callback") == "parse":
                # 对于分类页失败，总数+1
                self.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
                self.logger.error(
                    " in redicrect request error to failed pages url:%s, exception:%s, meta:%s" % (
                        request.url, reason, request.meta))

            raise IgnoreRequest("max redirections reached:%s" % reason)


class CustomCookiesMiddleware(DownloaderBaseMiddleware, CookiesMiddleware):
    def __init__(self, settings):
        DownloaderBaseMiddleware.__init__(self, settings)
        CookiesMiddleware.__init__(self, settings.getbool('COOKIES_DEBUG'))

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        obj = cls(crawler.settings)
        if not crawler.settings.getbool('COOKIES_ENABLED'):
            raise NotConfigured
        return obj

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        if 'dont_merge_cookies' in request.meta:
            return
        self.logger.debug("process in CustomCookiesMiddleware. ")
        headers = self.settings.get("HEADERS", {}).get(spider.name, {}).copy()
        cookiejarkey = request.meta.get("cookiejar", "default")
        jar = self.jars[cookiejarkey]
        if not request.meta.get("dont_update_cookies"):
            request.cookies.update(parse_cookie(headers.get("Cookie", "")))
        cookies = self._get_request_cookies(jar, request)

        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        for key in headers.keys():
            if key not in request.headers:
                request.headers[key] = [headers[key]]
        cl = request.headers.getlist('Cookie')
        if cl:
            msg = "Sending cookies to: %s" % request + os.linesep
            msg += os.linesep.join("Cookie: %s" % c for c in cl)
            self.logger.debug(msg)

    @process_response_method_wrapper
    def process_response(self, request, response, spider):

        if request.meta.get('dont_merge_cookies', False):
            return response

        self._debug_set_cookie(response, spider)
        cookiejarkey = request.meta.get("cookiejar", "default")
        jar = self.jars[cookiejarkey]
        jar.extract_cookies(response, request)
        return response


class RedisCacheCookieMiddleWare(DownloaderBaseMiddleware):
    def __init__(self, settings):
        DownloaderBaseMiddleware.__init__(self, settings)
        self.cookie = cookiejar.LWPCookieJar()
        self.lock = RLock()
        self.proxy = "local"

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        self.lock.acquire()
        try:
            if self.proxy != spider.proxy:
                self.proxy = spider.proxy
                index = random.randint(0, 9)
                cookie = spider.redis_conn.lindex(self.proxy, index)
                request.meta["captcha_index"] = index
                self.logger.debug("Captcha index %s of proxy: %s" % (index, self.proxy))
                if cookie:
                    self.cookie._really_load(StringIO(cookie.decode("utf-8")), "cookie", True, True)
            request.headers.pop('Cookie', None)
            self.cookie.add_cookie_header(WrappedRequest(request))
            self.logger.debug(
                "Add cookie [%s] header to %s. " % (request.headers.get("Cookie", ""), request.url))
        finally:
            self.lock.release()

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        self.lock.acquire()
        try:
            proxy = request.meta.get("proxy")
            index = request.meta.get("captcha_index", 0)
            if response.headers.get("Set-Cookie"):
                last_cookie = self.cookie.as_lwp_str(True, True)
                self.cookie.extract_cookies(WrappedResponse(response), WrappedRequest(request))
                self.logger.info("Extract cookies. ")
                while True:
                    spider.redis_conn.watch(proxy)
                    cookie = spider.redis_conn.lindex(self.proxy, index).replace(b"#LWP-Cookies-2.0\n", b"")
                    self.logger.info("Compare last cookie %s and current cookie  %s in redis. "%(last_cookie, cookie))
                    if last_cookie == cookie:
                        try:
                            spider.redis_conn.lset(proxy, index, "#LWP-Cookies-2.0\n%s" % self.cookie.as_lwp_str(True, True))
                            self.logger.info("Set new cookie to redis successfully. ")
                            break
                        except WatchError:
                            self.logger.info("Cookie in redis have beend changed. ")
                    else:
                        spider.redis_conn.unwatch(proxy)
                        last_cookie = cookie
                    self.cookie._really_load(StringIO(cookie.decode("utf-8")), "cookie", True, True)
            return response
        finally:
            self.lock.release()


class CustomRetryMiddleware(DownloaderBaseMiddleware, RetryMiddleware):
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TypeError, ValueError)

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)
        DownloaderBaseMiddleware.__init__(self, settings)

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    @process_exception_method_wrapper
    def process_exception(self, request, exception, spider):

        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            return self._retry(request, "%s:%s" % (exception.__class__.__name__, exception), spider)

        else:
            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])

            self.logger.error("in retry request error %s" % traceback.format_exc())
            # 记录重了
            # spider.crawler.stats.set_failed_download(request.meta, "%s unhandle error. " % exception)
            raise IgnoreRequest("%s:%s unhandle error. " % (exception.__class__.__name__, exception))

    def _retry(self, request, reason, spider):

        retries = request.meta.get('retry_times', 0) + 1

        if request.meta.get("if_next_page"):
            spider.change_proxy = True
            self.logger.warn("in _retry re-yield next_pages request: %s, reason: %s, proxy: %s. " % (
                request.url, reason, request.meta.get("proxy")))
            return request.copy()
        elif retries <= self.max_retry_times:
            spider.change_proxy = True
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            # our priority setup is different from super
            retryreq.meta['priority'] = retryreq.meta['priority'] + self.crawler.settings.get(
                "REDIRECT_PRIORITY_ADJUST")
            self.logger.warn("in _retry retries times: %s, re-yield request: %s, reason: %s, proxy: %s. " % (
            retries, request.url, reason, request.meta.get("proxy")))
            return retryreq

        else:
            # 错误信息记录出错的url ，而不是最初的url
            # request.meta["url"] = request.url

            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error(
                "in %s retry request error to failed pages url:%s, exception:%s, meta:%s" % (get_ip_address(),
                                                                                             request.url, reason,
                                                                                             request.meta))
            self.logger.warn("Gave up retrying %s (failed %d times): %s" % (request.url, retries, reason))
            raise IgnoreRequest("%s %s" % (reason, "retry %s times. "%retries))


class ProxyMiddleware(DownloaderBaseMiddleware):
    def __init__(self, settings):

        super(ProxyMiddleware, self).__init__(settings)
        proxy_list = settings.get("PROXY_LIST", "")
        self.proxy_list = [x for x in proxy_list.decode("utf-8").split('\n') if x.strip() and not x.strip().startswith("#")]

    def choice(self):
        if self.proxy_list:
            return random.choice(self.proxy_list)
        else:
            return None

    @process_requset_method_wrapper
    def process_request(self, request, spider):

        if spider.change_proxy:
            spider.proxy = None
            spider.change_proxy = False

        if self.proxy_list:
            spider.proxy = spider.proxy or self.choice()

        if spider.proxy:
            proxy = "http://" + spider.proxy
            request.meta['proxy'] = proxy
            self.logger.debug("use proxy %s to send request" % proxy, extra={"rasp_proxy": proxy})
            # #Use the following lines if your proxy requires authentication
            proxy_user_pass = self.settings.get("PROXY_PASSWORD")
            # # setup basic authentication for the proxy
            # #encoded_user_pass = base64.encodestring(proxy_user_pass)
            if proxy_user_pass:
                encoded_user_pass = base64.b64encode(proxy_user_pass)
                request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass


class LimitedUserAgentMiddleware(DownloaderBaseMiddleware):

    def __init__(self, settings):
        super(LimitedUserAgentMiddleware, self).__init__(settings)
        self.user_agent = self.settings.get("USER_AGENT")

    def process_request(self, request, spider):
        if self.user_agent:
            request.headers['User-Agent'] = self.user_agent
            self.logger.debug('User-Agent: {} {}'.format(request.headers.get('User-Agent'), request))
        else:
            self.logger.error('User-Agent: ERROR with user agent list')


class FixedRetryMiddleware(CustomRetryMiddleware):
    """
    过时
    """
    def __init__(self, settings):
        CustomRetryMiddleware.__init__(self, settings)
        # 出错后代理重试次数小于3次
        self.self_retry_count = 0

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        # 往父类参数传参一定要使用x=y的形式
        response = super(FixedRetryMiddleware, self).process_response(
            request=request, response=response, spider=spider)
        if isinstance(response, Request):
            # 如果返回request，则为异常情况，retry_count + 1
            self.self_retry_count += 1
        elif self.self_retry_count > 0:
            # 否则是正常情况 retry_count - 1
            self.self_retry_count -= 1
        return response

    @process_exception_method_wrapper
    def process_exception(self, request, exception, spider):
        if not request.meta.get('dont_retry', False):
            self.self_retry_count += 1
            return self.exception_retry(request, "%s:%s" % (exception.__class__.__name__, exception), spider)

    def exception_retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        if request.meta.get("if_next_page"):
            if self.self_retry_count > self.crawler.settings.getint("SELF_TIMEOUT_RETRY_TIMES", 3):
                spider.change_proxy = True
                self.self_retry_count = 0
            self.logger.warn("in _retry re-yield next_pages request: %s" % request.url)
            return request.copy()
        elif retries <= self.max_retry_times:
            if self.self_retry_count > self.crawler.settings.getint("SELF_TIMEOUT_RETRY_TIMES", 3):
                spider.change_proxy = True
                self.self_retry_count = 0
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            # our priority setup is different from super
            retryreq.meta['priority'] = retryreq.meta['priority'] + self.crawler.settings.get(
                "REDIRECT_PRIORITY_ADJUST")
            self.logger.warn(
                "In exception_retry retries times: %s, re-yield response.request: %s, reason: %s, proxy: %s" % (
                    retries, request.url, reason, request.meta.get("proxy")))
            return retryreq

        else:
            # 错误信息记录出错的url ，而不是最初的url
            # request.meta["url"] = request.url

            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error(
                "In %s exception_retry request error to failed pages url:%s, exception:%s, meta:%s. " % (
                    get_ip_address(), request.url, reason, request.meta))
            self.logger.warn("Gave up retrying %s (failed %d times): %s, Proxy: %s. " % (
                request.url, retries, reason, request.meta.get("proxy")))
            raise IgnoreRequest("%s %s" % (reason, "retry %s times. "%retries))


class NewFixedRetryMiddleware(CustomRetryMiddleware):
    # 增加了对TunnelError的重试
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed, TunnelError,
                           IOError, TypeError, ValueError)

    def _retry(self, request, reason, spider):

        retries = request.meta.get('retry_times', 0) + 1
        spider.change_proxy = True

        if request.meta.get("if_next_page"):
            self.logger.warn("in _retry re-yield next_pages request: %s, reason: %s, proxy: %s. " % (
                request.url, reason, request.meta.get("proxy")))
            return request.copy()

        elif retries <= self.max_retry_times:
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            # our priority setup is different from super
            retryreq.meta['priority'] = retryreq.meta['priority'] + self.crawler.settings.get(
                "REDIRECT_PRIORITY_ADJUST")
            self.logger.warn("in _retry retries times: %s, re-yield request: %s, reason: %s, proxy: %s. " % (
            retries, request.url, reason, request.meta.get("proxy")))
            return retryreq

        else:
            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error(
                "in %s retry request error to failed pages url:%s, exception:%s, proxy:%s" % (get_ip_address(),
                                                                                             request.url, reason,
                                                                                             request.meta.get("proxy")))
            self.logger.warn("Gave up retrying %s (failed %d times): %s" % (request.url, retries, reason))
            raise IgnoreRequest("%s %s" % (reason, "retry %s times. "%retries))


class CustomProxyMiddleware(ProxyMiddleware):

    def __init__(self, settings):

        super(ProxyMiddleware, self).__init__(settings)
        self.proxy_sets = self.settings.get("PROXY_SETS", "proxy_set").split(",")

    def choice(self):
        proxy = self.crawler.spider.redis_conn.srandmember(random.choice(self.proxy_sets))
        return proxy and proxy.decode("utf-8")

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        # if b"Cookie" in request.headers:
        #     del request.headers[b"Cookie"]
        # CHANGE_PROXY=True时，每次请求都会更换代理
        if self.settings.get("CHANGE_PROXY", False) or spider.change_proxy:
            spider.proxy = None
            spider.change_proxy = False

        if self.settings.getbool("NEED_JUMP"):
            spider.proxy = self.settings.get("PROXY_ADDR", "192.168.200.90:8087")
        else:
            if self.proxy_sets:
                spider.proxy = spider.proxy or self.choice()

        if spider.proxy:
            proxy = "http://"+spider.proxy
            request.meta['proxy'] = proxy
            self.logger.debug("use proxy %s to send request"%proxy, extra={"rasp_proxy": proxy})
            encoded_user_pass = base64.b64encode(self.settings.get("PROXY_ACCOUNT_PASSWORD").encode("utf-8"))
            request.headers['Proxy-Authorization'] = b'Basic ' + encoded_user_pass


class CaptchaManagerMiddleware(DownloaderBaseMiddleware):

    def __init__(self, settings):
        super(CaptchaManagerMiddleware, self).__init__(settings)
        self.cookie_path = self.settings.get("COOKIE_PATH", "cookies/")

        if not os.path.exists(self.cookie_path):
            os.mkdir(self.cookie_path)

        self.cookies = defaultdict(cookiejar.MozillaCookieJar)
        self.cookies_name_index = -1
        self.proxy = None
        self.load_cookies()
        self.bad_cookies = []
        self.captcha_field = CAPTCHA_FIELD.get(self.crawler.spidercls.name)

    def load_cookies(self):
        self.logger.debug("Load cookies ...")
        filename_re = os.path.join(
            self.cookie_path, "%s_%s*" % (self.crawler.spidercls.name, socket.gethostname())
        )
        filenames = glob.glob(filename_re)
        self.logger.debug("Find %s cookies. " % len(filenames))

        for filename in filenames:
            self._load_cookies(filename)
            self.proxy = filename.split("_")[2]

        self.cookie_keys = self.cookies.keys()
        self.logger.debug("%s cookies loaded. " % len(self.cookie_keys))

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def _load_cookies(self, filename):
        try:
            self.cookies_name_index += 1
            self.cookies[self.cookies_name_index].load(filename, True, True)
        except Exception:
            self.logger.debug("Haven't got a cookie yet. ")

            if self.cookies_name_index in self.cookies.keys():
                del self.cookies[self.cookies_name_index]
                self.cookies_name_index -= 1

            if os.path.exists(filename):
                os.remove(filename)

    @timeout(30, False)
    def parse_captcha(self, img_body):
        try:
            self.logger.debug("Start to parse CAPTCHA images. ")
            client = socket.socket()
            client.connect(
                (self.settings.get("CAPTCHA_ADDR", "192.168.200.58"), self.settings.get("CAPTCHA_PORT", 8887)))
            client.send(img_body)
            alphabet = client.recv(1024)
            client.close()
            return alphabet
        except Exception:
            self.logger.error("Error in parse_captcha. %s" % traceback.format_exc())

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        if self.captcha_field:
            if self.proxy:
                spider.proxy = self.proxy
                self.proxy = None
            if self.cookie_keys:
                cookie_name_index = random.choice(self.cookie_keys)
            elif self.bad_cookies:
                cookie_name_index = random.choice(self.bad_cookies)
            else:
                cookie_name_index = None
            if cookie_name_index is not None:
                request.headers.pop('Cookie', None)
                self.logger.debug("The using cookie index is %s. " % cookie_name_index)
                cookie = self.cookies[cookie_name_index]
                request.meta["cookie"] = cookie_name_index
                cookie.add_cookie_header(WrappedRequest(request))
                self.logger.debug("Add cookie [%s] header to %s. " % (request.headers.get("Cookie", ""), request.url))

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        if self.captcha_field:
            sel = self.check_captcha(response, request, spider)
            proxy = request.meta.get("proxy")
            if sel:
                self.handle_captcha(request, sel, proxy)
                return self.yield_new_request(request)
        return response

    def spider_closed(self, spider):
        self.logger.debug("Persistence cookies. ")
        filename_re = "%s_%s*" % (spider.name, socket.gethostname())
        [os.remove(x) for x in glob.glob(os.path.join(self.cookie_path, filename_re))]
        for index in self.cookie_keys:
            filename = os.path.join(
                self.cookie_path, "%s_%s_%s_%s" %
                                  (spider.name, socket.gethostname(), spider.proxy, index))
            self.save_cookie(self.cookies[index], filename)

    def save_cookie(self, cookie, filename):
        cookie.save(filename, True, True)

    def yield_new_request(self, request):
        new_request = request.copy()
        new_request.dont_filter = True
        self.logger.debug("In yield_new_request re-yield request: %s. " % request.url)
        return new_request

    @timeout(60, False)
    def get_captcha(self, img_url, proxy=None):
        try:
            self.logger.debug("get captcha images. ")
            opener = build_opener()
            if proxy:
                a_p = self.settings.get("PROXY_ACCOUNT_PASSWORD", "")
                proxy = 'http://%s%s'%(("%s@"%a_p if a_p else ""), proxy.lstrip("https://").lstrip("http://"))
                proxy = ProxyHandler({'https': proxy})
                opener.add_handler(proxy)
            resp = opener.open(img_url)
            img_body = resp.read()
            resp.close()
            return img_body
        except Exception:
            self.logger.error("Error in get_captcha: %s. " % traceback.format_exc())

    @timeout(60, False)
    def send_captcha(self, alphabet, k_v, request, sel, proxy):
        try:
            self.logger.debug("Start to send captcha request. ")
            self.cookies_name_index += 1
            cookiesHandler = HTTPCookieProcessor(self.cookies[self.cookies_name_index])
            opener = build_opener(cookiesHandler)
            if proxy:
                a_p = self.settings.get("PROXY_ACCOUNT_PASSWORD", "")
                proxy = 'http://%s%s'%(("%s@"%a_p if a_p else ""), proxy.lstrip("https://").lstrip("http://"))
                proxy = ProxyHandler({'https': proxy})
                opener.add_handler(proxy)
            args = dict([(k_v[i], k_v[i + 1]) for i in range(0, len(k_v), 2)])
            args.pop(u"amzn-pt", None)
            args["field-keywords"] = alphabet
            parts = urlparse(request.url)
            headers = request.headers.copy()
            if self.captcha_field.get("method") == "post":
                new_parts = parts._replace(path=get_val(self.captcha_field["captcha_form_url"], sel),
                                           query="")
                new_url = urlunparse(new_parts)
                req = Request(new_url, urlencode(args), headers=headers)
            else:
                new_parts = parts._replace(path=get_val(self.captcha_field["captcha_form_url"], sel), query=urlencode(args))
                new_url = urlunparse(new_parts)
                req = Request(new_url, headers=headers)
            self.logger.debug("send captcha to %s" % new_url)
            resp = opener.open(req)
            self.logger.debug("Captcha request have sent, response code:%s. " % resp.code)
            resp.close()
            if not self.cookies[self.cookies_name_index]._cookies:
                del self.cookies[self.cookies_name_index]
                self.cookies_name_index -= 1
                self.logger.error("Captcha recognized failed. ")
            else:
                self.cookie_keys = list(set(self.cookies.keys()) - set(self.bad_cookies))
                self.logger.debug("Got new captcha cookies. ")
            return True
        except Exception:
            self.logger.error("Error in send_captcha. Error: %s. " % traceback.format_exc())
            if self.cookies_name_index in self.cookies:
                del self.cookies[self.cookies_name_index]
                self.cookies_name_index -= 1

    def handle_captcha(self, request, sel, proxy=None):
        cookie_name_index = request.meta.get("cookie")
        if cookie_name_index is not None and cookie_name_index in self.cookie_keys:
            self.bad_cookies.append(cookie_name_index)
            self.cookie_keys.remove(cookie_name_index)
            self.logger.debug("Remove old cookies. ")
        if len(self.cookie_keys) < 1:
            img_url = get_val(self.captcha_field["image"], sel)
            self.logger.debug("Captcha path:%s. " % img_url)
            img_body = self.get_captcha(img_url, proxy)
            if img_body:
                alphabet = self.parse_captcha(img_body)
                self.logger.debug("Captcha have recognized to %s. " % alphabet)
            else:
                alphabet = None
                self.logger.error("Captcha download failed. ")
            if alphabet:
                k_v = get_val(self.captcha_field["key_value"], sel)
                self.send_captcha(alphabet, k_v, request, sel, proxy)

    def check_captcha(self, response, request, spider):
        sel = Selector(text=response.body)
        robot_checks = get_val(self.captcha_field["check"], sel)
        if robot_checks:
            self.logger.debug("Banned by %s: %s. " % (request.meta.get("proxy", "local"), request.url))
            return sel


class JomashopCpatchaMiddleware(DownloaderBaseMiddleware):

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        if spider.name == "jomashop" and response.status in [200, 405] and len(response.body) < 5000:
            if response.status == 200:
                return request
            else:
                return request.replace(url=request.meta["url"])
        return response


class AmazonSeleniumCaptchaMiddleware(CaptchaManagerMiddleware):

    @timeout(60, False)
    def web_drive(self, web, url):
        web.get(url)
        time.sleep(10)
        image_url = web.find_element_by_xpath('//div[@class="a-row a-text-center"]/img')
        captcha_field = web.find_element_by_name("field-keywords")
        return image_url, captcha_field

    def handle_captcha(self, request, sel, proxy=None):

        cookie_name_index = request.meta.get("cookie")
        if cookie_name_index is not None and cookie_name_index in self.cookie_keys:
            self.bad_cookies.append(cookie_name_index)
            self.cookie_keys.remove(cookie_name_index)
            self.logger.debug("Remove old cookies. ")
        if len(self.cookie_keys) < 1:
            url = urljoin(request.url, "/errors/validateCaptcha")
            image_url = None
            captcha_field = None
            from selenium import webdriver
            from selenium.common import Keys
            while True:
                if proxy:
                    proxy = proxy.lstrip("https://").lstrip("http://")
                    service_args = [
                        '--proxy=%s' % proxy,
                        '--proxy-type=https',
                        "--proxy-auth=%s" % self.settings.get("PROXY_ACCOUNT_PASSWORD")
                    ]
                    web = webdriver.PhantomJS(service_args=service_args)
                else:
                    web = webdriver.PhantomJS()
                try:
                    image_url, captcha_field = self.web_drive(web, url)
                    break
                except Exception:
                    self.logger.error("Error in webdriver send request: %s. "%traceback.format_exc())
                    web.close()
            src = image_url.get_attribute("src")
            image_body = self.get_captcha(src)
            if image_body:
                alphabet = self.parse_captcha(image_body)
                self.logger.debug("The parse result is:%s. "%alphabet)
                captcha_field.send_keys(alphabet)
                captcha_field.send_keys(Keys.RETURN)
                try:
                    c1 = web.get_cookie("x-amz-captcha-1").get(u"value")
                    c2 = web.get_cookie("x-amz-captcha-2").get(u"value")
                except Exception:
                    self.logger.error("Error in get cookie: %s. " % traceback.format_exc())
                    c1 = c2 = None
                domain = urlparse(url).netloc
                self.logger.debug("Retrive cookies %s and %s from proxy:%s. "%(c1, c2, proxy))
                if c1 and c2:
                    self.cookies_name_index += 1
                    c1 = self.gen_cookie("x-amz-captcha-1", c1, domain)
                    c2 = self.gen_cookie("x-amz-captcha-2", c2, domain)
                    self.cookies[self.cookies_name_index].set_cookie(c1)
                    self.cookies[self.cookies_name_index].set_cookie(c2)
                    self.cookie_keys = list(set(self.cookies.keys()))
                else:
                    self.logger.error("Captcha recognized failed. ")
            else:
                self.logger.error("Image download failed. ")

    @staticmethod
    def gen_cookie(key, val, domain):
        return cookiejar.Cookie(version=0,
                                name=key,
                                value=val,
                                domain=".%s"%domain,
                                path="/",
                                port=None,
                                port_specified=False,
                                domain_specified=True,
                                domain_initial_dot=False,
                                path_specified=True,
                                secure=False,
                                expires=None,
                                discard=False,
                                comment=None,
                                comment_url=None,
                                rest={},
                                rfc2109=False)


class AmazonCurlCaptchaRedisCachedMiddleware(DownloaderBaseMiddleware):

    def __init__(self, settings):
        super(AmazonCurlCaptchaRedisCachedMiddleware, self).__init__(settings)
        self.proxy_cookie_hash = self.settings.get("PROXY_COOKIE_HASH", "proxy_cookie")
        self.captcha_field = CAPTCHA_FIELD.get(self.crawler.spidercls.name)
        self.proxy = "local"
        self.cookie = CookieJar()
        self.cookie.clear = stats_wrapper(self.cookie.clear)
        self.session_timeout = self.settings.getint("SESSION_TIMEOUT", 500)
        self.last_session_timestamp = time.time()
        self.lock = RLock()

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        return cls(crawler.settings)

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        self.lock.acquire()
        try:
            if self.proxy != spider.proxy:
                self.proxy = spider.proxy
                index = random.randint(0, 9)
                cookie = spider.redis_conn.lindex(self.proxy, index)
                request.meta["captcha_index"] = index
                self.logger.debug("Captcha index %s of proxy: %s"%(index, self.proxy))
                if cookie:
                    self.cookie._really_load(StringIO(cookie.decode("utf-8")), "amazon.cookie", True, True)
                    self.cookie.clear_except("x-amz-captcha-1", "x-amz-captcha-2")
                    #self.clear_session_cookies()
            request.headers.pop('Cookie', None)

            # if time.time() - self.last_session_timestamp > self.session_timeout:
            #     self.clear_session_cookies()
            #     self.last_session_timestamp = time.time()
            self.cookie.add_cookie_header(WrappedRequest(request))
            self.logger.debug(
                "Add cookie [%s] header to %s. " % (request.headers.get("Cookie", ""), request.url))
        finally:
            self.lock.release()

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        sel = self.check_captcha(response, request, spider)
        proxy = request.meta.get("proxy")
        if sel:
            img_url = get_val(self.captcha_field["image"], sel)
            self.logger.debug("Captcha path:%s. " % img_url)
            img_body = self.get_captcha(img_url, proxy)
            if img_body:
                alphabet = self.parse_captcha(img_body)
                self.logger.debug("Captcha have recognized to %s. " % alphabet)
            else:
                alphabet = None
                self.logger.error("Captcha download failed. ")
            if alphabet:
                k_v = get_val(self.captcha_field["key_value"], sel)
                self.send_captcha(alphabet, k_v, request, sel, proxy, spider)
            return self.yield_new_request(request)
        else:
            self.cookie.extract_cookies(WrappedResponse(response), WrappedRequest(request))
            return response

    @timeout(60, False)
    def get_captcha(self, img_url, proxy=None):
        try:
            self.logger.debug("Get captcha images. ")
            opener = build_opener()
            if proxy:
                a_p = self.settings.get("PROXY_ACCOUNT_PASSWORD", "")
                proxy = 'http://%s%s' % (("%s@" % a_p if a_p else ""), proxy.lstrip("https://").lstrip("http://"))
                proxy = ProxyHandler({'https': proxy})
                opener.add_handler(proxy)
            resp = opener.open(img_url)
            img_body = resp.read()
            resp.close()
            return img_body
        except Exception:
            self.logger.error("Error in get_captcha: %s. " % traceback.format_exc())

    def yield_new_request(self, request):
        new_request = request.copy()
        new_request.dont_filter = True
        self.logger.debug("In yield_new_request re-yield request: %s. " % request.url)
        return new_request

    @timeout(30, False)
    def parse_captcha(self, img_body):
        try:
            self.logger.debug("Start to parse captcha images. ")
            client = socket.socket()
            client.connect(
                (self.settings.get("CAPTCHA_ADDR", "192.168.200.58"), self.settings.get("CAPTCHA_PORT", 8887)))
            client.send(img_body)
            alphabet = client.recv(1024)
            client.close()
            return alphabet
        except Exception:
            self.logger.error("Error in parse_captcha: %s. " % traceback.format_exc())

    def check_captcha(self, response, request, spider):
        sel = Selector(text=response.body)
        robot_checks = get_val(self.captcha_field["check"], sel)
        if robot_checks:
            self.logger.debug("Banned by %s: %s. " % (request.meta.get("proxy", "local"), request.url))
            return sel

    @timeout(60, False)
    def send_captcha(self, alphabet, k_v, request, sel, proxy, spider):
        try:
            self.logger.debug("Start to send captcha request. ")
            args = dict([(k_v[i], k_v[i + 1]) for i in range(0, len(k_v), 2)])
            args.pop(u"amzn-pt", None)
            args["field-keywords"] = alphabet
            parts = urlparse(request.url)
            headers = request.headers.copy()
            new_parts = parts._replace(path=get_val(self.captcha_field["captcha_form_url"], sel),
                                       query=urlencode(args))
            new_url = urlunparse(new_parts)
            sub = ""
            headers.pop("Cookie", 0)
            for header in headers.items():
                header = header[0].decode("utf-8") + ":" + (b"".join(header[1])).decode("utf-8")
                sub += " -H '%s' " % header
            if proxy:
                sub += (" -x %s -U %s" % (
                proxy.lstrip("https://").lstrip("http://"), self.settings.get("PROXY_ACCOUNT_PASSWORD")))
            cmd = "curl %s -sI '%s'" % (sub, new_url)
            self.logger.debug("Cmd: %s" % cmd)
            resp = os.popen(cmd)
            self.logger.debug("Send captcha to %s. " % new_url)
            buf = resp.read()
            self.logger.debug("Curl response header is %s, " % buf)
            codes = re.findall(r"HTTP/1\.(?:1|0) (\d{3})", buf)
            if "302" in codes:
                code = 302
            else:
                code = codes
            self.logger.debug("Captcha request have sent, response code:%s. " % code)
            if code == 302:
                cookies = re.findall(r"Set-Cookie: (.*?);", buf)
                if cookies:
                    # 主要为了删除
                    # self.cookie.clear()
                    self.lock.acquire()
                    try:
                        domain = urlparse(new_url).netloc
                        for cookie in cookies:
                            key, value = cookie.split("=", 1)
                            self.logger.debug("Combine cookie objects of %s. " % cookie)
                            cookie = self.gen_cookie(key, value, domain)
                            self.cookie.set_cookie(cookie)
                        index = request.meta.get("captcha_index", 0)
                        proxy = proxy and proxy.lstrip("https://").lstrip("http://")
                        self.logger.debug("Set captcha cookies to index %s of proxy %s. "%(index, proxy))

                        spider.redis_conn.lset(proxy, index, "#LWP-Cookies-2.0\n%s"%self.cookie.as_lwp_str(True, True))
                    finally:
                        self.lock.release()
                    self.logger.debug("Got new captcha cookies. ")
                    return True
                else:
                    self.logger.error("Haven't fount  Set-Cookies headers. ")
                    return False
            else:
                self.logger.error("Captcha recognize failed. ")
        except Exception:
            self.logger.error("Error in send_captcha: %s. " % traceback.format_exc())

    @staticmethod
    def gen_cookie(key, val, domain):
        return cookiejar.Cookie(version=0,
                                name=key,
                                value=val,
                                domain=".%s" % domain,
                                path="/",
                                port=None,
                                port_specified=False,
                                domain_specified=True,
                                domain_initial_dot=False,
                                path_specified=True,
                                secure=False,
                                expires=None,
                                discard=False,
                                comment=None,
                                comment_url=None,
                                rest={},
                                rfc2109=False)


class AmazonCurlCaptchaMiddleware(CaptchaManagerMiddleware):

    def __init__(self, settings):
        super(CaptchaManagerMiddleware, self).__init__(settings)
        self.cookie_path = self.settings.get("COOKIE_PATH", "cookies/")

        if not os.path.exists(self.cookie_path):
            os.mkdir(self.cookie_path)

        self.cookies = defaultdict(cookiejar.MozillaCookieJar)
        self.cookies_name_index = -1
        self.proxy_cookie_hash = {}
        self.proxy = None
        self.bad_cookies = []
        self.cookie_keys = []
        self.captcha_field = CAPTCHA_FIELD.get(self.crawler.spidercls.name)
        self.load_cookies()

    def load_cookies(self):
        self.logger.debug("Load cookies ...")
        filename_re = os.path.join(
            self.cookie_path, "%s_%s*" % (self.crawler.spidercls.name, socket.gethostname())
        )
        filenames = glob.glob(filename_re)
        self.logger.debug("Find %s cookies" % len(filenames))
        for filename in filenames:
            self._load_cookies(filename)
            self.proxy = filename.split("_")[2]
        self.cookie_keys.extend(self.cookies.keys())
        if self.proxy == "None":
            self.proxy = None
        self.proxy_cookie_hash[self.proxy] = {"cookie_keys": self.cookie_keys}
        self.logger.debug("%s cookies loaded. " % len(self.cookie_keys))

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def _load_cookies(self, filename):
        try:
            self.cookies_name_index += 1
            self.cookies[self.cookies_name_index].load(filename, True, True)
        except Exception:
            self.logger.debug("Haven't got a cookie yet. ")
            if self.cookies_name_index in self.cookies.keys():
                del self.cookies[self.cookies_name_index]
                self.cookies_name_index -= 1
            if os.path.exists(filename):
                os.remove(filename)

    @process_requset_method_wrapper
    def process_request(self, request, spider):
        if self.captcha_field:
            if self.proxy:
                spider.proxy = self.proxy
                self.proxy = None
            self.cookie_keys = self.proxy_cookie_hash.setdefault(
                spider.proxy.lstrip("https://").lstrip("http://") if spider.proxy else spider.proxy, {}).setdefault(
                "cookie_keys", [])
            self.bad_cookies = self.proxy_cookie_hash.setdefault(
                spider.proxy.lstrip("https://").lstrip("http://") if spider.proxy else spider.proxy, {}).setdefault(
                "bad_cookies", [])
            if self.cookie_keys:
                cookie_name_index = random.choice(list(self.cookie_keys))
            elif self.bad_cookies:
                cookie_name_index = random.choice(list(self.bad_cookies))
            else:
                cookie_name_index = None
            if cookie_name_index is not None:
                request.headers.pop('Cookie', None)
                self.logger.debug("The using cookie index is %s. " % cookie_name_index)
                cookie = self.cookies[cookie_name_index]
                request.meta["cookie"] = cookie_name_index
                cookie.add_cookie_header(WrappedRequest(request))
                self.logger.debug(
                    "Add cookie [%s] header to %s. " % (request.headers.get("Cookie", ""), request.url))

    @process_response_method_wrapper
    def process_response(self, request, response, spider):
        if self.captcha_field:
            sel = self.check_captcha(response, request, spider)
            proxy = request.meta.get("proxy")
            if sel:
                self.handle_captcha(request, sel, proxy)
                return self.yield_new_request(request)
        return response

    def spider_closed(self, spider):
        self.logger.debug("Persistence cookies. ")
        filename_re = "%s_%s*" % (spider.name, socket.gethostname())
        [os.remove(x) for x in glob.glob(os.path.join(self.cookie_path, filename_re))]
        for index in self.cookie_keys:
            filename = os.path.join(
                self.cookie_path, "%s_%s_%s_%s" %
                                  (spider.name, socket.gethostname(), spider.proxy, index))
            self.save_cookie(self.cookies[index], filename)

    def save_cookie(self, cookie, filename):
        cookie.save(filename, True, True)

    def handle_captcha(self, request, sel, proxy=None):
        self.cookie_keys = self.proxy_cookie_hash.setdefault(
            proxy.lstrip("https://").lstrip("http://") if proxy else proxy, {}).setdefault("cookie_keys",[])
        self.bad_cookies = self.proxy_cookie_hash.setdefault(
            proxy.lstrip("https://").lstrip("http://") if proxy else proxy, {}).setdefault("bad_cookies",[])
        cookie_name_index = request.meta.get("cookie")
        if cookie_name_index is not None and cookie_name_index in self.cookie_keys:
            self.bad_cookies.append(cookie_name_index)
            self.cookie_keys.remove(cookie_name_index)
            self.logger.debug("Remove old cookies. ")
        if len(self.cookie_keys) < 1:
            img_url = get_val(self.captcha_field["image"], sel)
            self.logger.debug("Captcha path:%s. " % img_url)
            img_body = self.get_captcha(img_url, proxy)
            if img_body:
                alphabet = self.parse_captcha(img_body)
                self.logger.debug("Captcha have recognized to %s. " % alphabet)
            else:
                alphabet = None
                self.logger.error("Captcha download failed. ")
            if alphabet:
                k_v = get_val(self.captcha_field["key_value"], sel)
                self.send_captcha(alphabet, k_v, request, sel, proxy)

    @timeout(60, False)
    def send_captcha(self, alphabet, k_v, request, sel, proxy):
        try:
            self.logger.debug("Start to send captcha request. ")
            args = dict([(k_v[i], k_v[i + 1]) for i in range(0, len(k_v), 2)])
            args.pop(u"amzn-pt")
            args["field-keywords"] = alphabet
            parts = urlparse(request.url)
            headers = request.headers.copy()
            new_parts = parts._replace(path=get_val(self.captcha_field["captcha_form_url"], sel),
                                       query=urlencode(args))
            new_url = urlunparse(new_parts)
            sub = ""
            for header in headers.items():
                header = header[0].decode("utf-8") +":" + (b"".join(header[1])).decode("utf-8")
                sub += " -H '%s' " % header
            if proxy:
                sub += (" -x %s -U %s"%(proxy.lstrip("https://").lstrip(
                    "http://"), self.settings.get("PROXY_ACCOUNT_PASSWORD")))
            cmd = "curl %s -sI '%s'" % (sub, new_url)
            self.logger.debug("Cmd: %s"%cmd)
            resp = os.popen(cmd)
            self.logger.debug("Send captcha to %s. " % new_url)
            buf = resp.read()
            self.logger.debug("Curl response header is %s" % buf)
            codes = re.findall(r"HTTP/1\.(?:1|0) (\d{3})", buf)
            if "302" in codes:
                code = 302
            else:
                code = 200
            self.logger.debug("Captcha request have sent, response code:%s. " % code)
            if code == 302:
                cookies = re.findall(r"Set-Cookie: (.*?);", buf)
                if cookies:
                    self.cookies_name_index += 1
                    domain = urlparse(new_url).netloc
                    for cookie in cookies:
                        key, value = cookie.split("=", 1)
                        self.logger.debug("Combine cookie objects of %s. "%cookie)
                        self.cookies[self.cookies_name_index].set_cookie(self.gen_cookie(key, value, domain))
                    self.cookie_keys.append(self.cookies_name_index) #list(set(self.cookies.keys()) - set(self.bad_cookies))
                    self.logger.debug("Got new captcha cookies. ")
                    return True
                else:
                    self.logger.error("Haven't fount  Set-Cookies headers. ")
                    return False
            else:
                self.logger.error("Captcha recognize failed. ")
        except Exception:
            self.logger.error("error in send_captcha. %s. " % traceback.format_exc())

    @staticmethod
    def gen_cookie(key, val, domain):
        return cookiejar.Cookie(version=0,
                                name=key,
                                value=val,
                                domain=".%s" % domain,
                                path="/",
                                port=None,
                                port_specified=False,
                                domain_specified=True,
                                domain_initial_dot=False,
                                path_specified=True,
                                secure=False,
                                expires=None,
                                discard=False,
                                comment=None,
                                comment_url=None,
                                rest={},
                                rfc2109=False)