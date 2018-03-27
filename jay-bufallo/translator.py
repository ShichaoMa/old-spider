#!/usr/bin/env python3.6
import json

from toolkit import chain_all, load_class, load_function
ItemEnricher = load_class("utils.components.ItemEnricher")


class Translator(ItemEnricher):
    """
        对explore类型的图片进行图片处理
    """
    name = "translator"

    class DummyResult(object):

        def __init__(self, dict):
            self.result = dict

        def get(self, **kwargs):
            return self.result

        @staticmethod
        def failed():
            return False

        @staticmethod
        def ready():
            return True

    def __init__(self):
        super(Translator, self).__init__()
        self.translate = load_function("utils.tasks.translate")

    def filter(self, item, trace):
        return item["item_type"].startswith("Bullet") and not item["cn"]

    @staticmethod
    def extract_values(item):
        try:
            values = json.loads(item["en"])
            if values and isinstance(values[0], list):
                values = chain_all(values)
        except Exception:
            if item["en"]:
                values = [item["en"]]
            else:
                values = []
        #item["value_length"] = len(values)
        return values

    def enrich(self, roc_item):
        values = "<1>".join(self.extract_values(roc_item))
        if values:
            roc_item["values"] = values
            return self.translate.delay(roc_item)
        else:
            roc_item["cn"] = ""
            return Translator.DummyResult({"items": [roc_item], "result": True})


if __name__ == "__main__":
    Translator().start()
