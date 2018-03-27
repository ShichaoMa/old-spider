# -*- coding:utf-8 -*-
from urllib2 import build_opener, HTTPCookieProcessor, Request
from cookielib import MozillaCookieJar
import cookielib
cookielib.debug = True
import logging
import sys

logger = logging.getLogger("cookielib")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


cookie = MozillaCookieJar()
opener = build_opener(HTTPCookieProcessor(cookie))
resp = opener.open("http://www.baihe.com/")

print "response headers:", resp.info().headers
print "cookies in cookie jar:", cookie._cookies
cookie.save("test.cookie", ignore_expires=True)

req = Request(url="http://www.baihe.com/")
cookie.add_cookie_header(req)
print "add cookie to a new request. ", req.unredirected_hdrs

