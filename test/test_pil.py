# -*- coding:utf-8 -*-
from PIL import Image


def check_image(func):
    """
    用来检查函数的第一个参数是图片路径还是图片地址，如果是地址则转换为图片
    :param func:
    :return:
    """
    def wrapper(*args):
        src_picture = args[0]
        need_close = True
        if not isinstance(src_picture, Image.Image):
            img = Image.open(src_picture)
        else:
            img = src_picture
            need_close = False
        args = list(args)
        args[0] = img
        func(*args)
        if need_close:
            img.close()

    return wrapper


def _convert_to(img, width, height):
    '''
    将原图片扩展或压缩成width×height, 背景色使用白色
    :param img: 原图片
    :param width:
    :param height:
    :return:
    '''
    w, h = img.size
    # 创建一个width x height的白色背景图层
    background = Image.new('RGBA', (width, height), (255, 255, 255))
    # 找出原图最长边
    src_max = max(w, h)
    # 确定目标图最长边
    dest_max = max(width, height)
    # 如果原图最长边大于目标图最长边，则对原图进行缩放
    if src_max > dest_max:
        rate = w / float(h)
        # 如果宽大于长
        if rate > 1:
            # 则以宽为目标宽，高进行比例缩放
            img = img.resize((width, int(width / rate)))
        else:
            # 否则以高为目标高，宽进行比例缩放
            img = img.resize((int(height * rate), height))
    w, h = img.size
    # 求出原图（或一次加工作的原图）在左上角在目标图中的位置
    pos_x, pos_y = (width - w) / 2, (height - h) / 2
    # 合并图层
    background.paste(img, (pos_x, pos_y))
    return background


@check_image
def convert_to(src_picture, dest_picture, width, height):
    '''
    将原图片扩展或压缩成width×height, 背景色使用白色
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :return:
    '''
    img = _convert_to(src_picture, width, height)
    img.show()
    img.save(dest_picture)


@check_image
def crop_to_center(src_picture, dest_picture, width, height):
    '''
    从中心截取 二分之一，缩放至 width x height
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :return:
    '''
    img = _crop_to_center(src_picture, width, height)
    img.show()
    img.save(dest_picture)


def _crop_to_center(img, width, height):
    '''
        从中心截取 二分之一，缩放至 width x height
        :param src_picture:
        :param dest_picture:
        :param width:
        :param height:
        :return:
        '''
    w, h = img.size
    # 找出最长边的二分之一作为目标图的标准边长
    src_max = max(w, h) / 2
    # 以最长边的二分之一为一半，计算左上角和右下角的坐标
    # 如果宽比标准边长小，则左上角的x坐标取0
    x0 = (w - src_max) / 2 if (w - src_max)/2 > 0 else 0
    # 如果高比标准边长小，则左上角的y坐标取0
    y0 = (h - src_max) / 2 if (h - src_max)/2 > 0 else 0
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
    # 缩放到目标边长
    return new.resize((width, height))


@check_image
def crop_to(src_picture, dest_picture, width, height, position="top"):
    '''
    将图片从水平位置或垂直位置中间截取一半
    并从这个半张图中截取最靠近图片中心位置的width x height的图片
    :param src_picture:
    :param dest_picture:
    :param width:
    :param height:
    :param position:
    :return:
    '''
    # 通过旋转来使用统一接口进行操作。
    if position == "bottom":
        img = src_picture.rotate(180)
        img = _crop_from_side_close_to_center(img, width, height).rotate(-180)
    elif position == "right":
        img = src_picture.rotate(90)
        img = _crop_from_side_close_to_center(img, width, height).rotate(-90)
    elif position == "left":
        img = src_picture.rotate(-90)
        img = _crop_from_side_close_to_center(img, width, height).rotate(90)
    else:
        img = _crop_from_side_close_to_center(src_picture, width, height)
    img.show()
    img.save(dest_picture)


def _crop_from_side_close_to_center(img, width, height):
    '''
    将图片从水平位置截取上半部分
    并从这个半张图中截取最靠近图片中心位置的width x height的图片
    :param img:
    :param width:
    :param height:
    :return:
    '''
    w, h = img.size
    # 高的一半
    half_y = h/2
    # 第一次截取上半部分
    first = img.crop((0, 0, w, half_y))
    # 如果截取后的高小于等于宽
    if half_y <= w:
        x0 = (w - half_y) / 2
        y0 = 0
        x1 = w -x0
        y1 = half_y
        second = first.crop((x0, y0, x1, y1))
    # 否则，截取后的高还是大于宽
    else:
        x0 = 0
        y0 = h/2 - w
        x1 = w
        y1 = half_y
        second = first.crop((x0, y0, x1, y1))
    return second.resize((width, height))


if __name__ == "__main__":
    import time, os
    t1 = time.time()
    # os.system("convert /mnt/nas/pi/images_store/amazon/713/169/25ee31861fc86de63c96b39d6d5468abc7/71316925ee31861fc86de63c96b39d6d5468abc7.jpg  -gravity center -crop 315x512 -resize 800x800 -extent 800x800 a.jpg")
    # os.system(
    #     "convert /mnt/nas/pi/images_store/amazon/713/169/25ee31861fc86de63c96b39d6d5468abc7/71316925ee31861fc86de63c96b39d6d5468abc7.jpg  -gravity center -crop 315x512 -resize 800x800 -extent 800x800 b.jpg")
    #convert_to("/mnt/nas/pi/images_store/eastbay/cf2/581/dbbdcb17bba544843c1aceedc803a970a0/cf2581dbbdcb17bba544843c1aceedc803a970a0.jpg", "b.jpg", 800, 800)
    #crop_to_center("/mnt/nas/pi/images_store/eastbay/cf2/581/dbbdcb17bba544843c1aceedc803a970a0/cf2581dbbdcb17bba544843c1aceedc803a970a0.jpg", "a.jpg", 800, 800)
    #convert_to("/mnt/nas/pi/images_store/amazon/713/169/25ee31861fc86de63c96b39d6d5468abc7/71316925ee31861fc86de63c96b39d6d5468abc7.jpg", "a.jpg", 800, 800)
    #t2 = time.time()
    #print 1111111111, t2 - t1
    # img = Image.open("/mnt/nas/pi/images_store/amazon/713/169/25ee31861fc86de63c96b39d6d5468abc7/71316925ee31861fc86de63c96b39d6d5468abc7.jpg")
    # img.show()
    # i = img.rotate(90)
    # i.show()
    crop_to("/mnt/nas/pi/images_store/eastbay/cf2/581/dbbdcb17bba544843c1aceedc803a970a0/cf2581dbbdcb17bba544843c1aceedc803a970a0.jpg", "a.jpg", 800, 800, "right")