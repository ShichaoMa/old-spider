import re

from toolkit import re_search


def main(curl_cmd):
    url = re.search(r"'(http.*?)'", curl_cmd).group(1)
    headers = dict(tuple(v.strip() for v in header.split(":", 1)) for header in re.findall(r"-H '(.*?)'", curl_cmd))
    form = re_search(r"--data '(.*?)'", curl_cmd)
    if form:
        data = dict(tuple(param.split("=", 1)) for param in form.replace("+", " ").split("&"))
    else:
        data = None
    return url, headers, data


if __name__ == "__main__":
    print(main("""curl 'http://fanyi.baidu.com/v2transapi' -H 'Pragma: no-cache' -H 'Origin: http://fanyi.baidu.com' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -H 'Accept: */*' -H 'Cache-Control: no-cache' -H 'X-Requested-With: XMLHttpRequest' -H 'Cookie: BAIDUID=4F96220C0E525C0A9E5217E375F91DEE:FG=1; PSTM=1516935041; PSINO=2; H_PS_PSSID=1428_21119_18559_17001_20930; BIDUPSID=4E10D76C5BCB983FE036C16DED9219E4; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; locale=zh; to_lang_often=%5B%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%2C%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%5D; REALTIME_TRANS_SWITCH=1; FANYI_WORD_SWITCH=1; HISTORY_SWITCH=1; SOUND_SPD_SWITCH=1; SOUND_PREFER_SWITCH=1; Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1517032917,1517032938,1517032947,1517032965; Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1517032965; from_lang_often=%5B%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%2C%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%5D' -H 'Connection: keep-alive' -H 'Referer: http://fanyi.baidu.com/?aldtype=16047' --data 'from=en&to=zh&query=what+a+fuck+day+it+is!&transtype=realtime&simple_means_flag=3&sign=58161.262144&token=a753535e844d86f9292916b16fb3f887' --compressed"""))