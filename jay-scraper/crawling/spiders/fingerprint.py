# -*- coding:utf-8 -*-
import re


FINGERPRINT = {
    # lambda 函数格式： 传入response_url, 返回唯一商品标识
    "amazon": lambda response_url: response_url[:response_url.find("ref")] if
    response_url.find("ref") != -1 else response_url,
    "eastbay": lambda response_url: getattr(
        re.search(r".*model:\d+/", response_url), "group", lambda x=response_url: x)(),
    "6pm": lambda response_url: getattr(
        re.search(r".*product/\d+", response_url), "group", lambda x=response_url: x)(),
    "zappos": lambda response_url: getattr(
        re.search(r".*product/\d+", response_url), "group", lambda x=response_url: x)(),
}