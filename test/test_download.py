# -*- coding:utf-8 -*-
import requests

from PIL import Image
from io import BytesIO

url = "https://images-na.ssl-images-amazon.com/images/I/81Y5TTTQD-L._SL1500_.jpg"

resp = requests.get(url=url, stream=True, proxies={"http": "http://longen:jinanlongen2016@192.168.104.160"})

with BytesIO() as f:
    for chunk in resp.iter_content(1024):
        f.write(chunk)
    Image.open(f).show()