# -*- coding:utf-8 -*-
import json
import requests
from urllib.parse import quote

def qq(src_data, proxies, src_template, self):
    """
    :param src_data: 原生数据
    :param proxies: 代理
    :param src_template: 原生数据模板
    :return: 结果
    """
    url, headers, data = ('http://fanyi.qq.com/api/translate',
                          {#'Pragma': 'no-cache', 'Origin': 'http://fanyi.qq.com',
                            'Accept-Encoding': 'gzip, deflate',
                           'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
                           'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                           'Accept': 'application/json, text/javascript, */*; q=0.01', 'Cache-Control': 'no-cache',
                           #'X-Requested-With': 'XMLHttpRequest',
                           #'Cookie': 'fy_guid=c3590212-ffc9-446a-9efa-e9f98f098903; pgv_info=ssid=s3880128728; ts_last=fanyi.qq.com/; ts_refer=www.baidu.com/link; pgv_pvid=2868933300; ts_uid=7186608412',
                           #'Connection': 'keep-alive', 'Referer': 'http://fanyi.qq.com/'
                            },
                          {'source': 'auto', 'target': 'en', 'sourceText': 'my%0Aname'})
    data["sourceText"] = quote(src_data)
    resp = requests.post(url, data=data, headers=headers)
    return src_template % tuple(record["targetText"] for record in json.loads(resp.text)["records"] if record.get("sourceText") != "\n")
