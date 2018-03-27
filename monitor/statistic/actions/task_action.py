# -*- coding:utf-8 -*-
import json
import time
import traceback

from gzip import GzipFile
from io import BytesIO
from bottle import Jinja2Template, HTTPResponse

from . import Application
from helper import _key
from helper.common import routing


class Task(Application):
    """
        task action
    """
    def __init__(self):
        self.captcha_queue = self.settings.get("CAPTCHA_QUEUE", "captcha_img_buf")

    @routing(path="/")
    def index(self):
        """
        任务统计页面主页
        :return:
        """
        return self.render(self.index)

    @routing()
    def datas(self):
        self.logger.info("Start to get datas. ")
        datas = self.db.get_datas()
        for k in datas:
            k["is_finished"] = self.db.check_finish("crawlid:%s" % k.get("crawlid", ""))
            if not k["is_finished"]:
                k["miss_pages"] = 0
        datas.sort(key=_key, reverse=True)
        new_datas = []
        for i in range(len(datas)):
            d = dict()
            for k, v in datas[i].items():
                if isinstance(k, bytes):
                    d[k.decode("utf-8")] = v
                else:
                    d[k] = v
            new_datas.append(d)
        self.logger.info("Start to zip datas. ")
        fileobj = BytesIO()
        f = GzipFile(mode="wb", fileobj=fileobj)
        f.write(json.dumps({"result": new_datas}).encode("utf-8"))
        f.close()
        fileobj.seek(0)
        data = fileobj.read()
        fileobj.close()
        self.logger.info("Start to send datas. ")
        return HTTPResponse(data, headers={"Content-Encoding": "gzip"})
        #return {"result": new_datas}

    @routing(path="/api/find")
    def find(self):
        """
        发现crawlid 状态
        :return:
        """

        crawlids = self.request.GET.get("crawlid").split("|")
        records = self.db.get_datas(crawlids)
        for record in records:
            record["status"] = "finished" if self.db.check_finish("crawlid:%s" % record.get("crawlid", "")) else "crawled"
        return {"records": records}

    @routing()
    def destroy(self):
        """
        彻底删除该记录
        :return:
        """
        try:
            crawlid = self.request.GET["crawlid"]
            spiderid = self.request.GET["spiderid"]
            self.db.destroy(crawlid, spiderid)
            return {"success": True}
        except Exception as e:
            self.logger.error("Error in destroy: %s" % traceback.format_exc())
            return {"success": False, "error": str(e)}

    @routing(path="/api/delete")
    def delete(self):
        """
        彻底删除该记录
        :return:
        """
        try:
            crawlid = self.request.GET["crawlid"]
            code = self.request.GET["code"]
            spiderid = self.codes[code]
            self.db.destroy(crawlid, spiderid)
            return {"success": True}
        except Exception as e:
            self.logger.error("Error in delete: %s"%traceback.format_exc())
            return {"success": False, "error": str(e)}

    @routing()
    def show_errors(self):
        """
        显示错误信息
        :return:
        """
        crawlid = self.request.GET["crawlid"]
        errors = self.db.get_failed_message(crawlid)
        return self.render(self.show_errors, keys=errors, flag="", template_adapter=Jinja2Template)