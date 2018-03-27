# -*- coding:utf-8 -*-
import re
import time
import datetime
import requests
import traceback

from scrapy import Selector


taobao = "首发,第一,第1,唯一,最,全球首家,全国首家,驰名商标,首选,顶级,顶尖,极端,极品,国家级,世界级,全球级,宇宙级,极品,极佳,终极,极致,绝佳,绝对," \
         "尖端,独家,军事,直降,领先,顶端,顶峰,巅峰,唯一,领袖品牌,市场主导品牌,首选品牌,中国公认名牌,绝无仅有,空前绝后,前所未有,史无前例,100%," \
         "NO 1,TOP 1,独一无二,一流,填补国内空白,国家免检,至尊,领袖品牌,王者,质量免检,免抽检,祖传,万能,无敌,之王,掌门人,独家配方,名牌,抄底," \
         "全网销量第一,王牌,销量冠军,永久,国际品质,驰名商标,中国名牌,CCTV,央视品牌,秒杀全网,无同款,淘宝之冠,淘宝之王,op品牌,无法超越,独有," \
         "国际一流,完美,必备,公安,军警,警察,部队,军队,特勤,07式"


jingdong = "最,最佳,最爱,最赚,最优秀,最好,最大,最多,最新,最高,最高级,最高端,最优惠,最好卖,第一,中国第一,世界第一,全网第一,销量第一,授权," \
          "NO  1,NO.  1,NO.1,NO1,,no1,no  1,no.1,No1,No  1,No.1,TOP  1,TOP.  1,TOP.1,TOP1,全国第一,一流,,国家级,世界级,国家级产品," \
          "全球级,高级,最低级,顶级,顶尖,尖端,顶级工艺,顶级服务,冠军,第一品牌,王牌,销量冠军,领袖,金牌,名牌,独家,绝无仅有,前无古人,极致,永久," \
          "100%,100％,100  %,100  ％,史无前例,万能,首发,军工,军用,军旅,军徽,军歌,国歌,国旗,国家领导,政治人物,,最后1天,,最后一小时,双十二," \
          "恐怖价,白菜价,跳楼价,牛逼,牛B,妆B,装逼,二奶,小三,小秘,秘书陪,骚男,骚年,屌丝,把妹,包妞,包养,裸聊,裸睡,裸奔,女人喊要,男人尖叫,爽一爽," \
          "用TA撸,泡妞必备,泡妞神器,放血,吐血,乳沟,骚男,骚年,脱光价,扒光低价,收妖,无节操,私处,电子狗,罚单,测速,碰瓷,违章,扣分,超速,讹诈,被讹," \
          "特供,专供,热荐,极品,避凶,辟邪,神丹,神仙,补五行,吸财,消灾,镇宅,剁手,抽烟,吸烟,一包烟,招商,招代理不卖了,世界末日,落网,卖肾,保肾," \
          "割肉价,坑爹,专家推荐,,领导乐了,户外者指定产品,,倒闭,老虎戴的表,独一,无二,正品,代购,直邮,直发,包邮,包税,首选,精确,精准,驰名,商标," \
          "热销,爆款,绝对,极端,万能,宇宙级,奢侈,军事,货到付款,热卖,疯抢,直降,清仓,让利,特价,领先,顶端,顶峰,巅峰,唯一,主导,公认,空前绝后,原价," \
          "巨星,大牌,真皮,高档,填补国内空白,国内空白,免检,至尊,王者,纯天然,超赚,免抽检,祖传,无敌,特效,之王,创领,掌门人,独有,独家，首个,首次," \
          "首款,著名,超级,卓越,传奇,完美,,超清,极好,极其,全方位,无可挑剔,精制,纯,先驱,代言,神仙,统统,每一个,任何,全球各地,前沿,必备,必须,必需," \
          "每个,闻名,空前,王,军刀,荣耀,明星,优质,奢华,终极,领导,优秀,资深,仅限,全网,秒杀,抢爆,豪礼,豪华,率先,色情,警用,弹簧刀,军警,永恒,知名," \
          "先锋,处方,edg,红珊瑚,高端,百搭,无与伦比,假一赔三,假一罚三,假一赔十,假一罚十,仅此1天,仅此,仅限1小时,安全,无毒副作用,无依赖,无效退款"


words_taobao = taobao.split(",")
#words_taobao = ["美国", "代购"]

words_jingdoing = jingdong.split(",")


def change(x):
    return "".join(x).strip()


f = open("result.csv", "a")


def send(x):
    f.write(",".join(x.values()))
    f.write("\n")


def gain():

    url = "http://192.168.200.66:6632/forfine/AllFine.aspx"
    data = {
    "ddlStore":"请选择",
    "SDate":(datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    "ddlUser":"请选择",
    "EDate":datetime.datetime.now().strftime("%Y-%m-%d"),
    "ddlShenhe":"所有",
    "BtnSelect":"查询时段",
    "txtPageUrl":"",
    "txtGoodsSku":"",
    "__VIEWSTATE":"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",
    "__EVENTVALIDATION":"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"
    }

    resp = requests.post(url, data=data, headers={"Cookie": "ASP.NET_SessionId=1es3tor5fuars0jm0zz5j5on"})

    sel = Selector(text=resp.text)

    return [{"shop_name": change(tr.xpath('td[1]/span/text()').extract()),
                "user": change(tr.xpath("td[2]/span/text()").extract()),
                "url": change(tr.xpath("td[4]/a[1]/@href").extract()),
                "item_no": change(tr.xpath("td[4]/a[1]/text()").extract())
                } for tr in sel.xpath("//table[@id='Tab']/tr")]


def check_taobao(record):
    url = record["url"]
    try:
        resp = requests.get(url)
        print("Url: %s response code: %s. "%(url, resp.status_code))
        sel = Selector(text=resp.text)
        title = change(sel.xpath('//div[@id="J_Title"]/h3/text()').extract())
        subtitle = change(sel.xpath('//p[@class="tb-subtitle"]/text()').extract())
        color = sel.xpath('//ul[@data-property="颜色分类"]/li').extract()
        feather = sel.xpath('//ul[@class="attributes-list"]/li/text()').extract()
        description_url = "https://" + change(sel.re(r"(desc\.alicdn\.com.*?)'"))
        des_sel = Selector(text=re.search(r"desc='([\S\s]+)';", requests.get(description_url).text).group(1))
        description = change(des_sel.xpath("//p/text()").extract())

        if len(color) > 14:
            record.update({"position": "color", "keyword":""})
            send(record)

        for key, val in {"title": title, "subtitle": subtitle, "description": description}.items():
            for word in words_taobao:
                if val.count(word):
                    record.update({"position": key, "keyword": word})
                    send(record)
    except Exception:
        print("Error in check_taoban: %s, \n url: %s"%(traceback.format_exc(), url))


def start():
    print("Start to find products after yesterday. ")
    records = gain()
    print("%s records found. "%len(records))
    for record in records:
        if record["url"].count("taobao"):
            print("Start check shop: %s, user: %s, url: %s, item_no: %s"%(record["shop_name"], record["user"], record["url"], record["item_no"]))
            check_taobao(record)
            #break
        time.sleep(1)


if __name__ == "__main__":
    start()