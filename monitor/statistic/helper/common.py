# -*- coding:utf-8 -*-
import os
import types
import signal

from functools import partial
from bottle import template, request, response,\
    redirect, app, run, route, BaseRequest

from .store import RedisRepository
from .server import CustomWSGIRefServer, WSGIServer, \
    ForkingWSGIServer, ThreadingWSGIServer, CustomWSGIRequestHandler


BaseRequest.MEMFILE_MAX = 102400000


def routing(**kwargs):
    """
    routing function
    :param kwargs:
    :return:
    """
    def out_wrapper(func):
        func.meta = kwargs
        return func
    return out_wrapper


class Common(object):
    """
        action common method base.
    """
    application = app()
    request = request
    response = response

    @classmethod
    def set_logger(cls, logger, settings):
        cls.logger = logger
        cls.settings = settings
        cls.db = RedisRepository(cls.settings.get("REDIS_HOST"), cls.settings.get_int("REDIS_PORT", 6379))
        cls.project_path = os.path.join(cls.settings.get("BASENAME"), cls.settings.get("PROJECT"))
        cls.codes = dict(tuple(reversed([y.strip() for y in x.split("\t")])) for x in open(
            os.path.join(cls.project_path, cls.settings.get("CODE", "code.list"))).read().strip().split("\n"))

    def render(self, view, **kwargs):
        view = view or kwargs.pop("views")
        path = None
        if isinstance(view, types.MethodType):
            path = os.path.join(self.project_path, "views",
                                "%s/%s.html"%(view.__self__.__class__.__name__.lower(), view.__name__))

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

    @classmethod
    def run(cls):
        signal.signal(signal.SIGINT, cls.stop)
        signal.signal(signal.SIGTERM, cls.stop)
        CustomWSGIRequestHandler.logger = cls.logger
        cls.server = CustomWSGIRefServer(
            app=cls.application,
            host=cls.settings.get("HOST"),
            port=cls.settings.get_int("PORT"),
            server_class=eval(cls.settings.get("SERVER_CLASS", "WSGIServer")),
            handler_class=CustomWSGIRequestHandler)
        run(server=cls.server, debug=cls.settings.get("DEBUG"), reloader=cls.settings.get("RELOAD"))

    @classmethod
    def stop(cls, *args):
        for instance in ActionMeta.instances:
            instance.close()
        cls.server.close()

    def close(self):
        pass


class LazyInstance:
    """
        action instance lazy load
    """
    def __init__(self, cls):
        self.__dict__["cls"] = cls
        self.__dict__["instance"] = None

    def __getattr__(self, attr):
        if self.instance is None:
            self.instance = self.cls()
        return getattr(self.instance, attr)

    def __setattr__(self, attr, value):
        if self.instance is None:
            self.__dict__["instance"] = self.cls()
        setattr(self.instance, attr, value)


class ActionMeta(type):
    """
        action meta class
    """
    instances = []

    def __new__(typ, clsname, bases, properties):
        """
        register routing path.
        :param clsname:
        :param bases:
        :param properties:
        :return:
        """
        action_cls = super(ActionMeta, typ).__new__(typ, clsname, bases, properties)
        action_instance = LazyInstance(action_cls)
        typ.instances.append(action_instance)
        for name, value in properties.items():
            if hasattr(value, "meta"):
                method, path = value.meta.get("method", ["GET"]), \
                               value.meta.get("path", "/%s/%s" % (clsname.lower(), name))
                callback = partial(value, self=action_instance)
                route(path=path, method=method, callback=callback)
        return action_cls