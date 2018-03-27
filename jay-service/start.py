#!/usr/bin/env python3.6
from bottle import route, app, run

from toolkit import load_module
from toolkit.monitors import Service as _Service

from statistic.server import CustomWSGIRefServer, CustomWSGIRequestHandler,\
    WSGIServer, ForkingWSGIServer, ThreadingWSGIServer


class Service(_Service):
    name = "service"
    server = None

    def __init__(self):
        super(Service, self).__init__()
        self.actions = set()
        self.load_action(self.settings.get("ACTIONS", "statistic.actions"))
        self.app = app()

    def load_action(self, action_module):
        mod = load_module(action_module)
        for name in dir(mod):
            if isinstance(getattr(mod, name), type):
                action = getattr(mod, name)(self.settings)
                for key in dir(action):
                    value = getattr(action, key)
                    if hasattr(value, "meta"):
                        method, path = value.meta.get("method", ["GET"]), \
                                       value.meta.get("path", "/%s/%s" % (name.lower(), key))
                        route(path=path, method=method, callback=value)
                self.actions.add(action)

    def start(self):
        CustomWSGIRequestHandler.set_logger(self.logger)
        self.server = CustomWSGIRefServer(
            app=self.app,
            host=self.settings.get("HOST"),
            port=self.settings.get_int("PORT"),
            server_class=eval(self.settings.get("SERVER_CLASS", "WSGIServer")),
            handler_class=CustomWSGIRequestHandler)
        run(server=self.server, debug=self.settings.get("DEBUG"), reloader=self.settings.get("RELOAD"))

    def stop(self, *args):
        self.alive = False
        for action in self.actions:
            action.close()
        self.server.close()


if  __name__ == "__main__":
    Service().start()
