# -*- coding:utf-8 -*-
import os
from PIL import Image


def show_all(path):
    for i, j, k in os.walk(path):
        for l in k:
            if l.lower().endswith("jpg"):
                with Image.open(os.path.join(i, l)) as f:
                    f.show()


def check_image(func):
    """
    用来检查函数的第一个参数是图片路径还是图片地址，如果是地址则转换为图片
    :param func:
    :return:
    """
    def wrapper(src_picture, dest_picture, width, height, position="top"):
        need_close = True
        try:
            if not isinstance(src_picture, Image.Image):
                img = Image.open(src_picture)
            else:
                img = src_picture
                need_close = False
            return func(img, dest_picture, width, height, position)
        finally:
            if need_close:
                img.close()
    return wrapper


def _convert_to(img, width, height):
    """
    将原图片扩展或压缩成width×height, 背景色使用白色
    :param img: 原图片
    :param width:
    :param height:
    :return:
    """
    w, h = img.size
    # 创建一个width x height的白色背景图层
    background = Image.new('RGB', (width, height), (255, 255, 255))
    # 找出原图最长边
    src_max = max(w, h)
    # 确定目标图最长边
    dest_max = max(width, height)
    # 如果原图最长边大于目标图最长边，则对原图进行缩放
    # if src_max > dest_max:
    rate = w / h
    # 如果宽大于高
    if rate > 1:
        # 则以宽为目标宽，高进行比例缩放
        img = img.resize((width, int(width / rate)))
    else:
        # 否则以高为目标高，宽进行比例缩放
        img = img.resize((int(height * rate), height))
    w, h = img.size
    # 求出原图（或第一次加工过的原图）的左上角在目标图中的位置
    pos_x, pos_y = (width - w) // 2, (height - h) // 2
    # 合并图层
    background.paste(img, (pos_x, pos_y))
    return background


@check_image
def convert_to(src_picture, dest_picture, width, height, *args):
    """
    将原图片扩展或压缩成width×height, 背景色使用白色
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :return:
    """
    img = _convert_to(src_picture, width, height)
    img.save(dest_picture)


@check_image
def crop_to_center(src_picture, dest_picture, width, height, *args):
    """
    从中心截取 二分之一，缩放至 width x height
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :return:
    """
    return _crop_to_center(src_picture, width, height)


def _crop_to_center(img, width, height):
    """
    从中心截取 二分之一，缩放至 width x height
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :return:
    """
    w, h = img.size
    # 找出最长边的二分之一作为目标图的标准边长
    src_max = max(w, h) // 2
    # 以最长边的二分之一为一半，计算左上角和右下角的坐标
    # 如果宽比标准边长小，则左上角的x坐标取0
    x0 = (w - src_max) // 2 if (w - src_max)//2 > 0 else 0
    # 如果高比标准边长小，则左上角的y坐标取0
    y0 = (h - src_max) // 2 if (h - src_max)//2 > 0 else 0
    # 如果宽不大于标准边长与左右边余量之和， 则右下角x坐标取w
    x1 = src_max + x0 if src_max + x0 < w else w
    # 如果高不大于标准边长与上下边余量之和， 则右下角y坐标取h
    y1 = src_max + y0 if src_max + y0 < h else h
    new = img.crop((x0, y0, x1, y1))
    w, h = new.size
    # 如果长， 高不同，证明上面四步判断中有命中，长，高没有全部达到标准边长，则进行空白填充
    if w != h:
        # 填充长度为宽和高的最大值
        max_size = max(w, h)
        new = _convert_to(new, max_size, max_size)
    if width:
        # 缩放到目标边长
        return new.resize((width, height))
    return new


@check_image
def crop_to(src_picture, dest_picture, width, height, position="top"):
    """
    将图片从水平位置或垂直位置中间截取一半
    并从这个半张图中截取最靠近图片中心位置的width x height的图片
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :param position:
    :return:
    """
    # 通过旋转来使用统一接口进行操作。
    if position == "bottom":
        img = src_picture.rotate(180)
        img = _crop_from_side_close_to_center(img, width, height).rotate(-180)
    elif position == "right":
        img = src_picture.rotate(90, 0, 1)
        img = _crop_from_side_close_to_center(img, width, height).rotate(-90)
    elif position == "left":
        img = src_picture.rotate(-90, 0, 1)
        img = _crop_from_side_close_to_center(img, width, height).rotate(90)
    else:
        img = _crop_from_side_close_to_center(src_picture, width, height)
    return img


def _crop_from_side_close_to_center(img, width, height):
    """
    将图片从水平位置截取上半部分
    并从这个半张图中截取最靠近图片中心位置的width x height的图片
    :param img:
    :param width:
    :param height:
    :return:
    """
    w, h = img.size
    # 高的一半
    half_y = h // 2
    # 第一次截取上半部分
    first = img.crop((0, 0, w, half_y))
    # 如果截取后的高小于等于宽
    if half_y <= w:
        x0 = (w - half_y) // 2
        y0 = 0
        x1 = w -x0
        y1 = half_y
        second = first.crop((x0, y0, x1, y1))
    # 否则，截取后的高还是大于宽
    else:
        x0 = 0
        y0 = h // 2 - w
        x1 = w
        y1 = half_y
        second = first.crop((x0, y0, x1, y1))
    if width:
        return second.resize((width, height))
    return second


if __name__ == "__main__":
    # paths =  [
		# {
		# 	"url" : "https://cws-zukx8h75btot52b0fbze2zjq3jmebvkm6ej.netdna-ssl.com/media/extendware/ewimageopt/media/inline/9f/e/armani-exchange-blue-active-analog-digital-mens-watch-ax1282-a8d.jpg",
		# 	"path" : "/home/ubuntu/imagess/certifiedwatchstore/bf/f0/02d3f6a8c7df86ee8689c8598fb4d3376c7a/bff002d3f6a8c7df86ee8689c8598fb4d3376c7a.jpg"
		# },
		# {
		# 	"url" : "https://cws-zukx8h75btot52b0fbze2zjq3jmebvkm6ej.netdna-ssl.com/media/extendware/ewimageopt/media/inline/e4/d/armani-exchange-blue-active-analog-digital-mens-watch-ax1282-f77.jpg",
		# 	"path" : "/home/ubuntu/imagess/certifiedwatchstore/f5/18/e0f2e5a2018c08cbea1aab11b991fbb95a40/f518e0f2e5a2018c08cbea1aab11b991fbb95a40.jpg"
		# }
    # ]
    # raw_input = globals().get("raw_input") or input
    # for path in paths:
    #     show_all(os.path.dirname(path.get("path")))
    #     i = raw_input("continue: ")
    # img = Image.open("/mnt/nas/pi/images_store/amazon/633/0c6/a2ef9b11be16d99aaf8675a91a79f5b0aa/6330c6a2ef9b11be16d99aaf8675a91a79f5b0aa.jpg")
    # img.show()
    # crop_to(img, "a.jpg", 800, 800, "left")
    # img.close()

    _convert_to(Image.open("/mnt/nas69/amazon/4d/f1/1196fbe6a3b59dec80b4137315e54382237c/4df11196fbe6a3b59dec80b4137315e54382237c.jpg"), 150, 150).save("a.jpg")
