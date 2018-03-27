# -*- coding:utf-8 -*-
import re
import os
from PIL import Image
from urllib import urlencode
from StringIO import StringIO
from scrapy import Selector
from urllib2 import build_opener
from scutils import method_timer

HEADERS = {
'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
'Accept-Encoding': "deflate, sdch",
'Accept-Language': "zh-CN,zh;q=0.8",
'Connection': "keep-alive",
'Host': "www.amazon.com",
'Upgrade-Insecure-Requests': "1",
'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
}

url = "https://www.amazon.com/errors/validateCaptcha"


def main():
    opener = build_opener()
    params = recognize(opener)

    while params:
        print "Send %s to %s"%(params, url)
        params = recognize(opener, params)


@method_timer.MethodTimer.timeout(60, "timeout")
def recognize(opener, params=None):
    cmd = gen_cmd(params)
    print "Curl cmd is: %s"%cmd
    resp = os.popen(cmd)
    code = 200
    if isinstance(params, dict):
        code = int(re.search(r"\d{3}", resp.readline()).group())
        print "Captcha html response code: %s" % code

    if code == 200:
        sel = Selector(text=resp.read())
        captcha_url = "".join(sel.xpath('//div[@class="a-row a-text-center"]/img/@src').extract())
        k_v = sel.xpath('//input[@type="hidden"]/@name|//input[@type="hidden"]/@value').extract()
        params = dict([(k_v[i], k_v[i + 1]) for i in range(0, len(k_v), 2)])
        image_resp = opener.open(captcha_url)
        print "Image response code: %s"% image_resp.code
        buf = StringIO(image_resp.read())
        img = Image.open(buf)
        img.show()
        captcha = raw_input("Please input captcha: ")
        params["field-keywords"] = captcha
        return params
    else:
        print re.findall(r"Set-Cookie: (.*?);", resp.read())


def gen_cmd(params):
    sub = ""
    for header in HEADERS.items():
        sub += " -H '%s' "%(":".join(header))
    if isinstance(params, dict):
        return "curl %s -sI '%s'"%(sub, url+"?"+urlencode(params))
    else:
        return "curl %s '%s'"%(sub, url)


if __name__ == "__main__":
    main()