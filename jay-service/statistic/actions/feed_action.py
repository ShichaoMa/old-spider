# -*- coding:utf-8 -*-
import json
import time
import requests

from bottle import HTTPResponse
from toolkit.managers import ExceptContext

from . import Application
from ..utils import routing


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
        with ExceptContext(errback=self.log_err):
            return self.render(self.index)

    @routing(path="/api/discover", method=["POST"])
    def api_discover(self):
        """
        roc 专用api抓取
        :return:
        """
        with ExceptContext(errback=self.log_err) as ec:
            data = self.request.POST.get("data")
            data = json.loads(data)
            crawlid = data.get("crawlid", time.strftime("%Y%m%d%H%M%S"))
            priority = int(data.get("priority", 1))
            spiderid = self.codes[data.get("source_site_code")]
            meta = data.get("meta", {})
            full = data.get("full", False)
            url = data.get("url")
            meta["full"] = full
            self.feed(meta, crawlid, priority, url, spiderid, "parse")
            self.db.redis_conn.hmset("crawlid:%s" % crawlid, {
                "total_pages": 0,
                "priority": priority,
                "type": "DISCOVER",
                "crawlid": crawlid,
                "spiderid": spiderid,
            })
            self.db.redis_conn.expire("crawlid:%s" % crawlid, self.settings.get_int("EXPIRE_TIME", 5 * 24 * 60 * 60))
            return {"success": True}
        return {"success": False, "error": ec.got_err}

    @routing(path="/api/enrich/tags", method=["POST"])
    def api_enrich_tags(self):
        """
        roc 专用api抓取
        :return:
        """
        with ExceptContext(errback=self.log_err) as ec:
            data = self.request.POST.get("data")
            data = json.loads(data)
            crawlid = data.get("crawlid", time.strftime("%Y%m%d%H%M%S"))
            priority = int(data.get("priority", 1))
            spiderid = self.codes[data.get("source_site_code")]
            meta = {"tags": {"tags": data.get("tags"), "source_site_code": data.get("source_site_code"),
                             "type": data.get("type").upper()}, "tag_target": data.get("tag_target")}
            url = data.get("url")
            self.feed(meta, crawlid, priority, url, spiderid, "parse")
            count = 0
            self.db.redis_conn.hmset("crawlid:%s" % crawlid, {
                "total_pages": count,
                "priority": priority,
                "type": "TAG",
                "crawlid": crawlid,
                "spiderid": spiderid,
            })
            self.db.redis_conn.expire("crawlid:%s" % crawlid, self.settings.get_int("EXPIRE_TIME", 5 * 24 * 60 * 60))
            return {"success": True}
        return {"success": False, "error": ec.got_err}

    @routing(path='/api/update', method=["POST"])
    def api_update(self):
        """
        blender调用的api
        :return:
        """
        with ExceptContext(errback=self.log_err) as ec:
            spiderid = self.codes[self.request.json["site"].upper()]
            # 将>0 改成 >200是为了应对amazon.DE和AMAZON site_code 同属一个spiderid: amazon，
            # 导致先放入amazon.de后，无法继续投放amazon的bug
            if self.db.redis_conn.zcard(self.settings.get("TASK_QUEUE_TEMPLATE") % spiderid) > 200:
                return HTTPResponse("The spider is working for other tasks. please update later. ", status=403)
            messages = self.request.json["messages"]
            crawlid = "roc_%s"%time.strftime("%Y%m%d%H%M%S")
            total_items = 0
            error_items = 0
            for message in messages:
                meta = message["meta"]
                meta["tags"] = message["tags"]
                meta["type"] = "UPDATE"
                meta["item_id"] = message["item_id"]
                if self.feed({"tags": meta}, crawlid, 1, meta["url"], spiderid, "parse_item"):
                    error_items += 1
                total_items += 1
            self.db.redis_conn.hmset("crawlid:%s" % crawlid, {
                "total_pages": total_items,
                "type": "UPDATE",
                "priority": 1,
                "spiderid": spiderid,
                "crawlid": crawlid,
            })
            self.db.redis_conn.expire("crawlid:%s" % crawlid, self.settings.get_int("EXPIRE_TIME", 12 * 60 * 60))
            return {"success": error_items < total_items, "error_items": error_items, "total_items": total_items}
        return {"success": False, "error": ec.got_err}

    @routing(path='/api/update')
    def update(self):
        with ExceptContext(errback=self.log_err) as ec:
            resp = requests.get("http://%s:%s/"%(
                self.settings.get("SCRAPY_HOST", "0.0.0.0"), self.settings.get_int("SCRAPY_PORT", 8888)),
                json=self.request.json)
            return json.loads(resp.text)
        return {"error": ec.got_err}


