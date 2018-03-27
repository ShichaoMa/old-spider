# -*- coding:utf-8 -*-


def get_rex_pat(keywords):
    rex_pat = ur"[^\u4e00-\u9fa5]+"

    for key in keywords:
        rex_pat = u"%s|" % key + rex_pat

    return rex_pat


def xpath_exchange(x):
    return "".join(x.extract()).strip()


class LazyFile(object):

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    @classmethod
    def open(cls, filename, mode):
        return cls(filename, mode)

    def write(self, buf):
        if not self.file:
            self.file = open(self.filename, mode=self.mode)
        self.file.write(buf)

    def close(self):
        if self.file and not self.file.closed:
            self.file.close()