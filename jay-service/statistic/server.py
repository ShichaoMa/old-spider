# -*- coding:utf-8 -*-
import socket
from socketserver import ForkingMixIn, ThreadingMixIn
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
from bottle import ServerAdapter


class CustomWSGIRequestHandler(WSGIRequestHandler):
    logger = None

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip and current date/time are prefixed to
        every message.

        """

        self.logger.info("%s - -  %s\n" %
                         (self.address_string(),
                          format%args))

    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger


class ForkingWSGIServer(ForkingMixIn, WSGIServer):
    pass


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass


class CustomWSGIRefServer(ServerAdapter):
    """
    wsgiref server adapter
    """
    def __init__(self, app, host, port, **options):
        super(CustomWSGIRefServer, self).__init__(host, port, **options)
        self.app = app
        self.server = None

    def run(self, app): # pragma: no cover

        class FixedHandler(CustomWSGIRequestHandler):

            def address_string(self): # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(*args, **kw):
                if not self.quiet:
                    return CustomWSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', WSGIServer)

        if ':' in self.host: # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:
                class server_cls(server_cls):
                    address_family = socket.AF_INET6
        server_cls.request_queue_size = 500
        self.server = make_server(self.host, self.port, app, server_cls, handler_cls)
        self.server.serve_forever()

    def close(self):
        if self.server:
            self.server.server_close()
        raise KeyboardInterrupt
