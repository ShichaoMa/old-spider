# -*- coding:utf-8 -*-
import pdb
from scrapy import Selector
from requests import get


def extract(url, rule, rule_type="xpath", proxies={}, headers={}):
    resp = get(url, proxies=proxies, headers=headers)
    print(resp.status_code)
    sel = Selector(text=resp.text)
    aaaaa = getattr(sel, rule_type)(rule)
    # import pdb
    # pdb.set_trace()
    print("Finish", aaaaa.extract())


if __name__ == "__main__":
    extract("https://www.ralphlauren.com/men-clothing-polo-shirts/classic-fit-soft-touch-polo/379580.html?cgid=men-clothing-polo-shirts&dwvar379580_colorname=Adirondack%20Lake&webcat=men%2Ftops%2FPolo%20Shirts",
            '//title', "xpath", headers={"Cookie": "_ga=GA1.3.1232746406.1516862392; _gid=GA1.3.662403225.1516862392; _gat_UA-70991458-4=1; crl8.fpcuid=f6e547dd-882d-4d09-ac0f-dc0275f97814"})#, proxies={"http": "http://longen:jinanlongen2016@mx14.headedeagle.com:12017"})

# from lxml import etree
# html="""
#     <div id="a">
#     left
#         <span id="b">
#         right
#             <ul>
#             up
#                 <li>down</li>
#             </ul>
#         east
#         </span>
#         west
#     </div>
# """
# #下面是没有用string方法的输出
# sel=etree.HTML(html)
# con=sel.xpath('//div[@id="a"]/text()')
# for i in con:
#     print(i)   #输出内容为left west
#
# data=sel.xpath('//div[@id="a"]')[0]
# info=data.xpath('string(.)')
# content=info.replace('\n','').replace(' ','')
# print(content)