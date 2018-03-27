# -*- coding:utf-8 -*-
import re


# 各网站图片处理方式
CONVERTIONS = {
    "amazon": {  # lambda 的参数image是color_image（单色）的一个元素
        "is_main": lambda image: [image.get('variant') == 'MAIN'],  # 判断是否为主图，详见ImageConvert::process_one_color_images
        "position": lambda image: image.get("hiRes") or "",  # 从image中找出图片url
    },
    "eastbay": {
        "is_main": lambda image: ["_a1_" in image, "_fr_" in image],
    },
    "zappos": {
        "is_main": lambda image: ["-p-" in image],
        "position": lambda image: image if isinstance(image, str) else "https://m.media-amazon.com/images/I/%s.jpg" % image["imageId"]
    },
    "6pm": {
        "is_main": lambda image: [image.get("type") == "MAIN"],
        "position": lambda image: "https://m.media-amazon.com/images/I/%s.jpg" % image["imageId"]
    },
    "finishline": {
        "is_main": lambda image: ["_fr" in image],
    },
    "jomashop": {
        "is_main": lambda image, pattern=re.compile(r"(?<!_\d)\.jpg"): [pattern.search(image)],
    },
    "ashford": {
        "is_main": lambda image: ["_FXA" in image],
    },
    "victoriassecret": {
        "position": lambda image: "https://dm.victoriassecret.com/%s/760x1013/%s.jpg"%(
            'p' if image['image'].count('tif/') else 'product', image.get("image")),
    },
    "nordstrom": {
        "position": lambda image: image.get("ImageMediaUri", {}).get("Zoom"),
    },
}