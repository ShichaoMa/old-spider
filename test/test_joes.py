import requests

headers = {#'Accept-Encoding': 'gzip, deflate, br',
           #'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
           #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Accept': '*/*'}

print(requests.post('https://www.joesnewbalanceoutlet.com/product/getInventoryQuantity', headers=headers,
                    data='__RequestVerificationToken=PmrbCQULx6Zpt5tklGNPPKTqyijPyB9oxDIy5o21YegKG9iB8EGlxz00iNRodKKM5SH5PpeyVU6EQiQxpXocUZk3bGLb_a6ytSCT7-wUj3A1&VariantID=WMD500P5-10.5-B').text)