# -*- coding:utf-8 -*-
import json
import time
import requests
import traceback

from bottle import HTTPResponse

from . import Application
from redis_feed import RedisFeed
from helper.common import routing
from helper import enrich, filebuf, feed

print(RedisFeed)

class Feed(Application):
    """
        feed action.
    """
    @routing()
    def index(self):
        """
        任务添加主页
        :return:
        """
        return self.render(self.index)

    @routing(method="POST")
    def crawl(self):
        """
        普通抓取， 将来会过时
        :return:
        """
        type = self.request.POST["type"]
        crawlid = self.request.POST["crawlid"]
        spiderid = self.request.POST["spiderid"]
        priority = int(self.request.POST["priority"] or 1)
        urls = self.request.POST["urls"]
        urlsfile = self.request.POST["urlsfile"]
        if urlsfile:
            urlsfile = filebuf(urlsfile.file.read())
        else:
            urlsfile = None
        fullurl = True if type == "1" else False
        multiple = True if type == "3" else False
        getitems = True if type == "4" else False
        if type == "5":
            urlsfile = filebuf(urls.replace("    ", "\n"))
            fullurl = True
        meta = None
        if spiderid == "amazon" and type in ["0", "5"]:
            meta = {"extend": False}
        rf = RedisFeed(crawlid=crawlid, spiderid=spiderid,
                       priority=priority, url=urls,
                       urls_file=urlsfile, full_url=fullurl,
                       multiple=multiple, update=not getitems,
                       port=self.settings.get_int("REDIS_PORT"),
                       host=self.settings.get("REDIS_HOST"),
                       custom=self.settings.get("CUSTOM_REDIS"),
                       show=False, meta=meta)
        rf.start()
        return self.redirect(self.index)

    @routing(path="/api/feed", method=["POST"])
    def api_feed(self):
        """
        roc 专用api抓取
        :return:
        """
        try:
            data = self.request.POST.get("data")
            data = json.loads(data)
            type = data.get("type")
            spiderid = None
            crawlid = data.get("crawlid", time.strftime("%Y%m%d%H%M%S"))
            priority = int(data.get("priority", 1))
            if type == "explore":
                spiderid = self.codes[data.get("source_site_code")]
                meta = data.get("meta")
                full = data.get("full", False)
                url = data.get("url")
                meta["full"] = full
                meta["type"] = type
                feed(self.db, meta, crawlid, priority, url, spiderid, "parse")
                count = 0
            else:
                extend = data.get("extend", True)
                products = data.get("products")
                count = 0
                for line in products:
                    spiderid = self.codes[line.get("source_site_code")]
                    if not spiderid.count("amazon"):
                        extend = True
                    m = line.get("meta")
                    m["type"] = type
                    if extend:
                        feed(self.db, m, crawlid, priority, line.get("product_url"), spiderid, "parse_item")
                        count += 1
                    else:
                        m["extend"] = False
                        stuffix = "com"
                        if spiderid != "amazon":
                            spiderid, stuffix = spiderid.split(".", 1)
                        tmp = 'https://www.amazon.%s/gp/product/%%s/ref=twister_dp_update?ie=UTF8&psc=1' % stuffix
                        for sku in line.get("skus"):
                            feed(self.db, m, crawlid, priority, tmp%sku, spiderid, "parse_item")
                            count += 1
            self.db.redis_conn.hmset("crawlid:%s" % crawlid, {
                "total_pages": count,
                "type": type,
                "priority": priority,
                "crawlid": crawlid,
                "spiderid": spiderid,
            })
            self.db.redis_conn.expire("crawlid:%s" % crawlid, self.settings.get_int("EXPIRE_TIME", 5 * 24 * 60 * 60))
            return {"success": True}
        except Exception:
            self.logger.error("Error in api_feed: Error %s. "%traceback.format_exc())
            return {"success": False, "error_info": traceback.format_exc()}

    @routing(path='/api/update', method=["POST"])
    def api_update(self):
        """
        blender及upc_finder调用的api
        :return:
        """
        try:
            spiderid = self.codes[self.request.json["site"].lower()]
            # 将>0 改成 >200是为了应对amazon.de和amazon site_code 同属一个spiderid: amazon，
            # 导致先放入amazon.de后，无法继续投放amazon的bug
            if self.db.redis_conn.zcard("%s:item:queue"%spiderid) > 200:
                return HTTPResponse("The spider is working for other tasks. please update later. ", status=403)
            messages = self.request.json["messages"]
            crawlid = "roc_%s"%time.strftime("%Y%m%d%H%M%S")
            base ={"tags": {"source_site_code": self.request.json["site"].upper()}, "type": "update", "all_sku": True}
            total_pages = 0
            for message in messages:
                meta = message
                meta.update(base)
                feed(self.db, meta, crawlid, 1, message["data"]["url"], spiderid, "parse_item")
                total_pages += 1
            self.db.redis_conn.hmset("crawlid:%s" % crawlid, {
                "total_pages": total_pages,
                "type": "update",
                "priority": 1,
                "spiderid": spiderid,
                "crawlid": crawlid,
            })
            self.db.redis_conn.expire("crawlid:%s" % crawlid, self.settings.get_int("EXPIRE_TIME", 12 * 60 * 60))
            return {"success": True}
        except Exception:
            self.logger.error("Error in api_update: Error %s. "%traceback.format_exc())
            return {"success": False, "error_info": traceback.format_exc()}

    @routing(path='/api/update')
    def update(self):
        try:
            resp = requests.get("http://%s:%s/"%(
                self.settings.get("SCRAPY_HOST", "0.0.0.0"), self.settings.get_int("SCRAPY_PORT", 8888)),
                json=self.request.json)
            return json.loads(resp.text)
        except Exception as e:
            self.logger.error("Error in update: Error %s. " % traceback.format_exc())
            return {"error": str(e)}