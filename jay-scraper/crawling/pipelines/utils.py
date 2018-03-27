# -*- coding:utf-8 -*-
import re

from toolkit import re_search
from toolkit.managers import ExceptContext


def format_price(price, regex=re.compile(r"([\d\.]+)")):
    price = str(price)
    if price.count("EUR"):
        price = price.replace(".", "").replace(",", ".")
    with ExceptContext():
        return float(re_search(regex, price.replace(",", ""), default=0))
    return 0


class References(list):

    def __init__(self, seq=()):
        self.extend(seq)

    def append(self, p_object):
        if p_object and not self.contains(p_object):
            super(References, self).append(p_object)

    def extend(self, iterable):
        for p_object in iterable:
            self.append(p_object)

    def contains(self, p_object, keys=("item_id", "item_type")):
        for p in self:
            return_value = True
            for key in keys:
                return_value &= p[key] == p_object[key]
                if not return_value:
                    break
            if return_value:
                return return_value
        return False


class SafeSet(set):

    def pop(self):
        try:
            return super(SafeSet, self).pop()
        except KeyError:
            return None


class SafeList(list):

    def pop(self, index=0):
        try:
            return super(SafeList, self).pop(0)
        except IndexError:
            return None
