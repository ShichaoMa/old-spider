#!/usr/bin/env python3.6
from toolkit import load_class, load_function

ItemEnricher = load_class("utils.components.ItemEnricher")


class Painter(ItemEnricher):
    """
        对explore类型的图片进行图片处理
    """
    name = "painter"

    def __init__(self):
        super(Painter, self).__init__()
        self.convert = load_function("utils.tasks.convert")

    def filter(self, item, trace):
        return item["item_type"] == "Image" and item["path"]

    def enrich(self, roc_item):
        return self.convert.delay(roc_item)


if __name__ == "__main__":
    Painter().start()
