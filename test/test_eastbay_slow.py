# -*- coding:utf-8 -*-
import time
url = "http://www.eastbay.com/_-_/keyword-vans"

HEADERS = {#'Referer': 'http://www.eastbay.com/_-_/keyword-vans?Nao=120&cm_PAGE=120',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
            'Accept-Encoding': 'gzip,deflate'}
from requests import get


for i in range(20):

    resp = get(url, headers=HEADERS, timeout=30)

    print(resp.status_code)
    time.sleep(2)