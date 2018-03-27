#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Chuande Wang on 16/6/17
import os
import pytesseract

from PIL import Image
from io import BytesIO


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

#
# def turn(bytesio):
#     new_bytesio = BytesIO()
#     with Image.open(bytesio) as image:
#
#         image.save(new_bytesio, "jpeg")
#     return new_bytesio


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


def main(filename):
    root, dirs, files = os.walk(filename)
    for name in files:
        print(os.path.abspath(name))


if __name__ == '__main__':
    print(tesseract_image(Image.open("/home/ubuntu/Downloads/aaa.jpg")))
