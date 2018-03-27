#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import os
import time
import json
import openpyxl
import datetime
import traceback
from redis import Redis
from bottle import route, run, request


os.chdir(os.path.dirname(os.path.abspath(__file__)))

redis_conn = Redis("192.168.200.150")


def extract_excel(path):
    try:
        print("Start to process file: %s"%path)
        wb = openpyxl.load_workbook(path, read_only=True)
        sheet = wb.active
        # pdb.set_trace()
        datas = dict()
        title = []
        got_title = False
        for row in sheet.rows:
            data = dict()
            for index, cell in enumerate(row):
                if not got_title:
                    title.append(cell.value)
                else:
                    data[title[index]] = cell.value
            if data:
                datas.setdefault(
                    data.get("Catalog Number") or
                    data["parent_productid"] or
                    data["productid"], []).append(data)
            else:
                got_title = True
        wb.close()
        print("Extract file %s finished. "%path)
        return datas
    except Exception:
        print("Extract file %s failed ."%path)
        traceback.print_exc()


@route('/')
def index():
    return """<html>
        <head><title>areatrend导入程序</title></header>
        <body>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input name="file" type="file"  />
                <input type="submit" value="按天文件提交" />
                &nbsp;&nbsp;&nbsp;<span>上次提交时间:</span><span>%s</span>
            </form>
            <form action="/upload_price" method="post" enctype="multipart/form-data">
                <input name="file" type="file"  />
                <input type="submit" value="按周文件提交" />
            </form>
        </body>
    </html>"""% datetime.datetime.fromtimestamp(float(redis_conn.get("areatrend:update") or 0)).strftime("%Y-%m-%d %H:%M:%S")


@route('/upload_price', method=["POST"])
def upload_price():
    file = request.files["file"]
    file.save("areatrend_price.xlsx", overwrite=True)
    datas = extract_excel("areatrend_price.xlsx")
    key = "areatrend:price"
    redis_conn.hmset(key, dict((k, json.dumps(v)) for k, v in datas.items()))
    return """<html><script>
                alert("成功");
                document.location = '/';
        </script></html>"""


@route('/upload', method=["POST"])
def upload():
    file = request.files["file"]
    file.save("areatrend.xlsx", overwrite=True)
    datas = extract_excel("areatrend.xlsx")
    new_datas = dict()
    for key, value in datas.items():
        for v in value:
            base_price = redis_conn.hget("areatrend:price", v["productid"])
            if base_price:
                base_price = json.loads(base_price)[0]
            else:
                base_price = {}
            v["cost"] = min(float(v["cost"]), float(base_price.get("Offer Price", 1000000)))
        new_datas[key] = json.dumps(value)
    key = "areatrend:product"
    redis_conn.hmset(key, new_datas)
    redis_conn.set("areatrend:update", time.time())
    return """<html><script>
            alert("成功");
            document.location = '/';
    </script></html>"""


if __name__ == "__main__":
    import sys
    run(host=sys.argv[1], port=sys.argv[2])