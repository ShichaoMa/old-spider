# -*- coding:utf-8 -*-
import re
headers = """Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.8,en;q=0.6
Cache-Control:no-cache
Connection:keep-alive
Content-Length:216
Content-Type:application/x-www-form-urlencoded; charset=UTF-8
Cookie:OUTFOX_SEARCH_USER_ID=-301382631@10.169.0.84; JSESSIONID=aaaJDxdCKIa6cajAMN65v; OUTFOX_SEARCH_USER_ID_NCOO=710027979.2475773; SESSION_FROM_COOKIE=www.baidu.com; UM_distinctid=15e7ab3a2a95e7-08491109d7acdb-31637e01-1fa400-15e7ab3a2aa9b9; ___rl__test__cookies=1505297466814
Host:fanyi.youdao.com
Origin:http://fanyi.youdao.com
Pragma:no-cache
Referer:http://fanyi.youdao.com/
User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36
X-Requested-With:XMLHttpRequest"""
headers = dict(line.split(":", 1) for line in headers.split("\n"))
print(headers)

print( "-H '", "' -H '".join("%s=%s"%(k, v) for k, v in headers.items()), "'")




def parser_headers(headers):
    return dict(tuple(i.strip() for i in header.split(":", 1)) for header in re.findall("-H '(.*?)'", headers))


if __name__ == "__main__":
    print(parser_headers("""-H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.8,en;q=0.6' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Referer: https://www.amazon.com/Converse-Unisex-Chuck-Taylor-Sneakers/dp/B0059NGJSU/ref=lp_679260011_1_1?s=apparel&ie=UTF8&qid=1505447322&sr=1-1&nodeID=679260011&psd=1&th=1&psc=1'  -H 'Connection: keep-alive' -H 'Cache-Control: no-cache'"""))