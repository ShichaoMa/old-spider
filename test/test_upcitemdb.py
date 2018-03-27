# -*- coding:utf-8 -*-
import requests

url = "http://www.upcitemdb.com/upc/740352447596"

resp = requests.get(url)

import pdb

pdb.set_trace()

from scrapy import Selector
print(len(resp.text))

sel = Selector(text=resp.text)

print()

# '//dt[contains(text(), "EAN")]/following-sibling::dd[1]/text()'
# '//dt[contains(text(), "Size")]/following-sibling::dd[1]/text()'
# '//dt[contains(text(), "Color")]/following-sibling::dd[1]/text()'
# '//dt[contains(text(), "Model")]/following-sibling::dd[1]/text()'
# '//td/a'