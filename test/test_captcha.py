# -*- coding:utf-8 -*-
import os
import time
import socket
import traceback
import pytesseract

from io import BytesIO
from PIL import Image
from requests import get
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

service_args = [
                '--proxy=192.168.200.90:8123',
                '--proxy-type=http'
            ]

def tesseract_image(image):
    return pytesseract.image_to_string(image, config='--tessdata-dir . -psm 10', lang='image')


# 图片x轴的投影，如果有数据（黑色像素点）值为1否则为0
def get_projection_x(image):
    p_x = [0 for x in range(image.size[0])]
    for w in range(image.size[1]):
        for h in range(image.size[0]):
            # print(image.getpixel((h,w)))
            if image.getpixel((h, w)) == 0:
                p_x[h] = 1
    return p_x


# 获取分割后的x轴坐标点
# 返回值为[起始位置, 长度] 的列表
def get_split_seq(projection_x):
    res = []
    for idx in range(len(projection_x) - 1):
        p1 = projection_x[idx]
        p2 = projection_x[idx + 1]
        if p1 == 1 and idx == 0:
            res.append([idx, 1])
        if p1 == 0 and p2 == 0:
            continue
        elif p1 == 1 and p2 == 1:
            res[-1][1] += 1
        elif p1 == 0 and p2 == 1:
            res.append([idx + 1, 1])
        else:  # p1 == 1 and p2 == 0
            continue
    return res


# 分割后的图片，x轴分割后，同时去掉y轴上线多余的空白
def split_image(image, split_seq=None):
    if split_seq is None:
        split_seq = get_split_seq(get_projection_x(image))
    length = len(split_seq)
    imgs = [[] for i in range(length)]
    res = []
    for w in range(image.size[1]):
        line = [image.getpixel((h, w)) for h in range(image.size[0])]
        for idx in range(length):
            pos = split_seq[idx][0]
            llen = split_seq[idx][1]
            l = line[pos:pos + llen]
            imgs[idx].append(l)
    for idx in range(length):
        datas = []
        height = 0
        for data in imgs[idx]:
            flag = False
            for d in data:
                if d == 0:
                    flag = True
            if flag:
                height += 1
                datas += data
        child_img = Image.new('L', (split_seq[idx][1], height))
        child_img.putdata(datas)
        res.append(child_img)

    return res

def binarized(image_buffer):
    # 网络上的图片转换成Image对象
    with Image.open(BytesIO(image_buffer)) as image:
        # 灰度化处理
        # 有很多种算法，这里选择rgb加权平均值算法
        image = image.convert("RGB")
        gray_image = Image.new('1', image.size)
        width, height = image.size
        raw_data = image.load()
        for x in range(width):
            for y in range(height):
                value = raw_data[x, y]
                value = value[0] if isinstance(value, tuple) else value
                if value < 1:
                    gray_image.putpixel((x, y), 0)
                else:
                    gray_image.putpixel((x, y), 255)
        image_word_list = split_image(gray_image)
        word_list = []
        for word in image_word_list:
            sigle_word = tesseract_image(word)
            word_list.append(sigle_word)
        word_string = ''.join(word_list)
        if not os.path.exists("amazon_images"):
            os.mkdir("amazon_images")
        image.close()
        return word_string

def main():
    url = "https://www.amazon.com/errors/validateCaptcha"
    web = webdriver.PhantomJS(service_args = service_args)
    image_url = None
    captcha_field = None
    while True:
        try:
            web.get(url)
            time.sleep(10)
            image_url = web.find_element_by_xpath('//div[@class="a-row a-text-center"]/img')
            captcha_field = web.find_element_by_name("field-keywords")
            break
        except Exception:
            traceback.print_exc()
            web.close()
    src = image_url.get_attribute("src")
    image_body = get_captcha(src)
    alphabet = parse_captcha(image_body)
    captcha_field.send_keys(alphabet)
    captcha_field.send_keys(Keys.RETURN)
    c1 = web.get_cookie("x-amz-captcha-1")
    c2 = web.get_cookie("x-amz-captcha-2")


def get_buffer(url):
    buffer = b""
    for chunk in get(url, stream=True).iter_content(1024):
        buffer += chunk
    return buffer


def parse_captcha(url):
    client = socket.socket()
    client.connect(("", 8887))
    client.send(get_buffer(url))
    alphabet = client.recv(1024)
    client.close()
    return alphabet


# def bound(img):
#     raw_data = img.load()
#     new_data = []
#     for line in range(img.size[1]):
#         pix = 0
#         new_line = []
#         while pix < img.size[0]-1:
#             p1 = raw_data[pix, line]
#             p2 = raw_data[pix+1, line]
#             if p1 == 255 and p2 == 0:
#                 new_line.append(0)
#             elif p1 == 255 and p2 == 255:
#                 new_line.append(p1)
#             elif p1 == 0 and p2 == 0:
#                 new_line.append(p1)
#             else:#  p1 == 0 and p2 == 255:
#                 new_line.append(0)
#                 new_line.append(0)
#                 pix += 1
#             pix += 1
#         new_data += new_line
#     new_img = Image.new('L', img.size)
#     new_img.putdata(new_data)
#     return new_img


def parse_port(url):
    with Image.open(BytesIO(get_buffer(url))) as image:
        image = image.convert("RGB")
        gray_image = Image.new('1', image.size)
        width, height = image.size
        raw_data = image.load()
        image.close()
        for x in range(width):
            for y in range(height):
                value = raw_data[x, y]
                value = value[0] if isinstance(value, tuple) else value
                if value < 1:
                    gray_image.putpixel((x, y), 0)
                else:
                    gray_image.putpixel((x, y), 255)
        num = pytesseract.image_to_string(gray_image)
        result = guess(num)
        if result:
            return result
        else:
            new_char = list()
            for i in num:
                if i.isdigit():
                    new_char.append(i)
                else:
                    new_char.append(guess(i))
            return "".join(new_char)
        # image_word_list = split_image(gray_image)
        # new_char = list()
        # for img in image_word_list:
        #     nums = pytesseract.image_to_string(img)
        #     for i in nums:
        #         if i.isdigit():
        #             new_char.append(i)
        #         else:
        #             new_char.append(guess(i))
        # import pdb
        # pdb.set_trace()
        # return "".join(new_char)


def guess(word):
    try:
        mapping = {
            "b": "8",
            "o": "0",
            "e": "8",
            "s": "9",
            "51234": "61234",
            "3737": "9797",
            "3000": "9000",
            "52385": "62386",
        }
        return mapping[word.lower()]
    except KeyError:
        if len(word) == 1:
            print(word)


def bz(image_buffer):
    # 网络上的图片转换成Image对象
    with Image.open(BytesIO(image_buffer)) as image:
        # 灰度化处理
        # 有很多种算法，这里选择rgb加权平均值算法
        image = image.convert("RGB")
        gray_image = Image.new('1', image.size)
        width, height = image.size
        raw_data = image.load()
        for x in range(width):
            for y in range(height):
                value = raw_data[x, y]
                value = value[0] if isinstance(value, tuple) else value
                if value < 1:
                    gray_image.putpixel((x, y), 0)
                else:
                    gray_image.putpixel((x, y), 255)
        return gray_image


def download(img_url, name):
    bz(get_buffer(img_url)).save("%s.png"%name)


if __name__ == "__main__":
    print(parse_port("https://proxy.mimvp.com/common/ygrandimg.php?id=2&port=NmDiVmtvapW12cDgwMTAO0O"))
    #download("https://proxy.mimvp.com/common/ygrandimg.php?id=2&port=MmDiFmtvapW12cDgxMjMO0O", 8123)
