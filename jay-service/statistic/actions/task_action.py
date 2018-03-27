# -*- coding:utf-8 -*-
import json

from io import BytesIO
from gzip import GzipFile
from bottle import Jinja2Template, HTTPResponse

from toolkit.managers import ExceptContext

from . import Application
from ..utils import routing


class Task(Application):
    """
        task action
    """

    @routing(path="/")
    def index(self):
        """
        任务统计页面主页
        :return:
        """
        with ExceptContext(errback=self.log_err):
            return self.render(self.index)

    @routing()
    def datas(self):
        with ExceptContext(errback=self.log_err):
            datas = self.db.get_datas()
            datas.sort(key=lambda x: x.get("update_time", "1970-01-01 00:00:00"), reverse=True)
            fileobj = BytesIO()
            f = GzipFile(mode="wb", fileobj=fileobj)
            f.write(json.dumps({"result": datas}).encode("utf-8"))
            f.close()
            fileobj.seek(0)
            data = fileobj.read()
            fileobj.close()
            return HTTPResponse(data, headers={"Content-Encoding": "gzip"})

    @routing(path="/api/find")
    def find(self):
        """
        发现crawlid 状态
        :return:
        """
        with ExceptContext(errback=self.log_err):
            crawlids = self.request.GET.get("crawlid").split("|")
            return {"records": self.db.get_datas(crawlids)}

    @routing()
    def destroy(self):
        """
        彻底删除该记录
        :return:
        """
        with ExceptContext(errback=self.log_err):
            crawlid = self.request.GET["crawlid"]
            spiderid = self.request.GET["spiderid"]
            self.db.destroy(crawlid, spiderid)
            return {"success": True}
        return {"success": False, "error": str(e)}

    @routing(path="/api/delete")
    def delete(self):
        """
        彻底删除该记录
        :return:
        """
        with ExceptContext(errback=self.log_err):
            crawlid = self.request.GET["crawlid"]
            code = self.request.GET["code"]
            spiderid = self.codes[code]
            self.db.destroy(crawlid, spiderid)
            return {"success": True}
        return {"success": False, "error": str(e)}

    @routing()
    def show_errors(self):
        """
        显示错误信息
        :return:
        """
        with ExceptContext(errback=self.log_err):
            crawlid = self.request.GET["crawlid"]
            errors = self.db.get_failed_message(crawlid)
            return self.render(self.show_errors, keys=errors, flag="", template_adapter=Jinja2Template)