# -*- coding:utf-8 -*-
import requests


for i in range(10000):
    resp = requests.post("http://localhost:5000/")
    print("%sth response, code: %s, text: %s. "%(i, resp.status_code, resp.text))