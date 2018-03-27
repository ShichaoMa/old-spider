#-*- coding:gbk -*-
import re
import sys
import json
import time
import random
import pymssql
import urllib
import urllib2
import traceback
import cookielib

from google_translate import GoogleTranslator, ProxySelector


SEND_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        "Accept-Language": "en-US,en;q=0.5",
    }


proxy_list = [
    'http://longen:jinanlongen2016@192.168.101.160:12017',
    'http://longen:jinanlongen2016@192.168.102.160:12017',
    'http://longen:jinanlongen2016@192.168.103.160:12017',
    'http://longen:jinanlongen2016@192.168.104.160:12017',
    'http://longen:jinanlongen2016@192.168.105.160:12017',
    'http://longen:jinanlongen2016@192.168.106.160:12017',
    'http://longen:jinanlongen2016@192.168.107.160:12017',
    'http://longen:jinanlongen2016@192.168.108.160:12017',
    'http://longen:jinanlongen2016@192.168.109.160:12017',
    'http://longen:jinanlongen2016@192.168.121.160:12017',
    'http://longen:jinanlongen2016@192.168.122.160:12017',
    'http://longen:jinanlongen2016@192.168.123.160:12017',
    'http://longen:jinanlongen2016@192.168.124.160:12017',
    'http://longen:jinanlongen2016@192.168.126.160:12017',
    'http://longen:jinanlongen2016@192.168.127.160:12017',
    'http://longen:jinanlongen2016@192.168.131.160:12017',
    'http://longen:jinanlongen2016@192.168.132.160:12017',
    'http://longen:jinanlongen2016@192.168.133.160:12017',
    'http://longen:jinanlongen2016@192.168.134.160:12017',
    'http://longen:jinanlongen2016@192.168.135.160:12017',
    'http://longen:jinanlongen2016@192.168.136.160:12017',
    'http://longen:jinanlongen2016@192.168.137.160:12017',
    'http://longen:jinanlongen2016@192.168.138.160:12017',
    'http://longen:jinanlongen2016@192.168.139.160:12017',
    'http://longen:jinanlongen2016@192.168.141.160:12017',
    'http://longen:jinanlongen2016@192.168.142.160:12017',
    'http://longen:jinanlongen2016@192.168.143.160:12017',
    'http://longen:jinanlongen2016@192.168.144.160:12017',
]

invalidate_proxy = {}


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))


def post(req):
    while True:
        try:
            proxy = random.choice(proxy_list)
            while proxy in invalidate_proxy and invalidate_proxy.get(proxy) > time.time() - 60 * 60:
                proxy = random.choice(proxy_list)
            if proxy in invalidate_proxy:
                del invalidate_proxy[proxy]
            opener.add_handler(urllib2.ProxyHandler({"http": proxy}))
            buf = opener.open(req, timeout=20).read()
            return json.loads(buf)
        except urllib2.URLError:
            print "将非法代理 %s放到暂存列表中" % proxy
            invalidate_proxy[proxy] = time.time()
            traceback.print_exc()
        except ValueError:
            print "将出验证码的代理 %s放到暂存列表中" % proxy
            invalidate_proxy[proxy] = time.time()
            traceback.print_exc()


def translate_all(src, website):
    return eval("translate_all_%s(src)"%website)


def translate_all_youdao(src):
    translate_params = {'keyfrom': 'fanyi.web', 'i': 'apple', 'doctype': 'json', 'action': 'FY_BY_CLICKBUTTON',
                        'ue': 'UTF-8', 'xmlVersion': '1.8', 'type': 'AUTO', 'typoResult': 'true'}
    pattern = re.compile(r"(^|>)([\s\S]*?)(<|$)")
    ls = re.findall(pattern, src.replace("\n", ""))
    url = "http://fanyi.youdao.com/translate"
    src_data = "\n".join(filter(lambda y:y.strip(), map(lambda x:x[1], ls)))
    if src_data.strip():
        translate_params['i'] = src_data
        src = src.replace("%", "%%")
        src_template = re.sub(pattern, lambda x: "%s%s%s"%(x.group(1), "%s" if x.group(2).strip() else "", x.group(3)), src)
        req = urllib2.Request(url, urllib.urlencode(translate_params), SEND_HEADERS)
        data =  map(lambda y: ("".join(map(lambda x: x["tgt"], y))).encode("gbk", "ignore"), post(req)["translateResult"])
        return src_template%tuple(data)
    else:
        return src


def translate_all_baidu(src):
    translate_params = {'from': 'en', 'to': 'zh', 'transtype': 'realtime', 'simple_means_flag': 3}
    pattern = re.compile(r"(^|>)([\s\S]*?)(<|$)")
    ls = re.findall(pattern, src.replace("\n", ""))
    url = "http://fanyi.baidu.com/v2transapi"
    src_data = "\n".join(filter(lambda y:y.strip(), map(lambda x:x[1], ls)))
    if src_data.strip():
        translate_params['query'] = src_data
        src = src.replace("%", "%%")
        src_template = re.sub(pattern, lambda x: "%s%s%s"%(x.group(1), "%s" if x.group(2).strip() else "", x.group(3)), src)
        req = urllib2.Request(url, urllib.urlencode(translate_params), SEND_HEADERS)
        data = post(req)

        data = "".join(map(lambda x: x["src_str"], data["trans_result"]['phonetic'])).split("\n")
        return src_template%tuple(data)
    else:
        return src


def translate_all_google(src):
    pattern = re.compile(r"(^|>)([\s\S]*?)(<|$)")
    ls = re.findall(pattern, src.replace("\n", ""))
    src_data = filter(lambda y:y.strip(), map(lambda x:x[1], ls))
    if src_data:
        src = src.replace("%", "%%")
        src_template = re.sub(pattern, lambda x: "%s%s%s"%(x.group(1), "%s" if x.group(2).strip() else "", x.group(3)), src)
        data = translate_google(src_data)
        return src_template%tuple(data)
    else:
        return src


def translate_google(src):
    ps = ProxySelector()
    ps._proxy_list = proxy_list
    gt = GoogleTranslator(ps)
    gt.MAX_INPUT_SIZE = 1024000
    result = gt.translate(src, "zh-CN")
    if result:
        return result
    else:
        return gt.translate("name", "zh-CN", src_lang="en")


def main(website="youdao"):
    conn = None
    try:
        conn = pymssql.connect(server="192.168.200.67", user="NewPeople", password="cpz0410LHL", database="LE_JDDK",
                               charset="utf8")
        cur = conn.cursor()
        cur.execute("select itemENContent, itemId from LE_Item where (itemCNContent is NULL or itemCNContent = '' or itemCNContent = 'null') and itemId = '4291542'")
        allnum = cur.fetchall()
        if not allnum:
            print "data had been translated completely."
        for index, itemNums in enumerate(allnum):
            if itemNums[0]:
                while True:
                    try:
                        cur.execute("update LE_Item set itemCNContent=%s where itemId=%s",
                                    ( translate_all(itemNums[0].encode("utf-8"), website), itemNums[1]))
                        conn.commit()
                        print "当前正在翻译的ID:%d  还有%d条未翻译。" % (itemNums[1], len(allnum)-index-1)
                    except urllib2.URLError, e:
                        print "网络异常，正尝试重连... %s"%e
                        continue
                    except Exception:
                        print itemNums[0].encode("utf-8")
                        traceback.print_exc()
                    break
    except KeyboardInterrupt:
        print "exit..."
    finally:
        if conn:
            conn.close()


def search(id):
    conn = pymssql.connect(server="192.168.200.66", user="NewPeople", password="cpz0410LHL", database="LE_JDDK",
                           charset="utf8")
    cur = conn.cursor()
    cur.execute("select itemENContent, itemCNContent, itemId from LE_Item where itemCNContent = 'null' and itemParentASIN='%s'"%id)
    print cur.fetchall()
    conn.close()
   
if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
    #print translate_all("""<pstyle="line-height:200%">44mm Case</p></li></ul></div></div><div><h2>Additionaldetails</h2><ulclass="additional-list"><li>Chronograph</li><li>Date</li></ul></div></div>""", "google").encode("utf-8")
    #search('jacoYA129411')

