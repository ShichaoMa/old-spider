import requests

headers = {
    #'Pragma': 'no-cache',
    #'Origin': 'http://fanyi.baidu.com',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    #'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    #'Accept': '*/*',
    #'Cache-Control': 'no-cache',
    #'X-Requested-With': 'XMLHttpRequest',
    'Cookie':
        'BAIDUID=B2A57C69A108D46D922586ADFD28E77A:FG=1; '
        #'BIDUPSID=B2A57C69A108D46D922586ADFD28E77A; '
        #'PSTM=1516862842;'
        #' BDORZ=FFFB88E999055A3F8A630C64834BD6D0; '
        #'PSINO=2; '
        #'H_PS_PSSID=1459_19033_21109_18560_22075;'
        #' locale=zh;'
        #' Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1516867515; '
        #'Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1516867515; '
        #'to_lang_often=%5B%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%2C%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%5D; '
        #'REALTIME_TRANS_SWITCH=1; '
        #'FANYI_WORD_SWITCH=1;'
        #' HISTORY_SWITCH=1; '
        #'SOUND_SPD_SWITCH=1; '
        #'SOUND_PREFER_SWITCH=1; '
        #'from_lang_often=%5B%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%2C%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%5D',
    #'Connection': 'keep-alive',
    #'Referer': 'http://fanyi.baidu.com/'
    }

url ='http://fanyi.baidu.com/v2transapi'

body = {'from': 'en', 'to': 'zh', 'query': 'name', 'transtype': 'realtime', 'simple_means_flag': '3', 'sign': '106415.359582', 'token': 'a9f46df0a74fb5e5e7c5943979a01ed3'}

print(requests.post(url, body, headers=headers).text)