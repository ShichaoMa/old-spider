import types
import pickle

from os.path import dirname, join
from abc import ABC, abstractmethod
from redis.exceptions import RedisError
from bottle import request, response, template, redirect, BaseRequest

from toolkit.managers import ExceptContext

from .persistence import RedisStore
from .utils import cache_property


BaseRequest.MEMFILE_MAX = 102400000


class Common(ABC):
    """
        action common method base.
    """
    request = request
    response = response

    @property
    @abstractmethod
    def settings(self):
        pass

    @property
    @abstractmethod
    def logger(self):
        pass

    @cache_property
    def project_path(self):
        return dirname(__file__)

    @cache_property
    def codes(self):
        return dict(x.split("\t") for x in open(
            join(self.project_path, self.settings.get("CODE", "code.list"))).read().split("\n"))

    @cache_property
    def db(self):
        return RedisStore(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT", 6379))

    def render(self, view, **kwargs):
        view = view or kwargs.pop("views")
        path = None
        if isinstance(view, types.MethodType):
            path = join(self.project_path, "views", "%s/%s.html"%(view.__self__.__class__.__name__.lower(), view.__name__))

        if not view:
            path = kwargs.pop("path")
        if path:
            with open(path) as f:
                return template(f.read(), **kwargs)
        return view

    @staticmethod
    def redirect(view):
        if isinstance(view, types.MethodType):
            view = view.__name__
        return redirect(view)

    def feed(self, meta, crawlid, priority, url, spiderid, callback):
        data = {"url": url.strip(),
                "crawlid": crawlid,
                "spiderid": spiderid,
                "callback": callback,
                "priority": priority}
        data.update(meta)
        queue_name = self.settings.get("TASK_QUEUE_TEMPLATE", "%s:newitem:queue") % spiderid
        with ExceptContext(RedisError) as ec:
            self.db.redis_conn.zadd(queue_name, pickle.dumps(data), -priority)
            return 0
        return ec.err_info
