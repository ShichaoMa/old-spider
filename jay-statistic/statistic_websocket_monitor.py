#!/usr/bin/env python3.6
import time
import json
import traceback

from threading import Thread

from toolkit import load_class
from toolkit.monitors import Service

SimpleWebSocketServer = load_class("simple_websocket_server.SimpleWebSocketServer")
WebSocket = load_class("simple_websocket_server.WebSocket")
RedisRepository = load_class("statistic.helper.store.RedisRepository")


class StatisticWebsocket(Service):
    name = "statistic_websocket"

    def __init__(self):
        super(StatisticWebsocket, self).__init__()
        self.clients = dict()
        self.timeouts = dict()
        self.rr = RedisRepository(self.settings.get("REDIS_HOST", "192.168.200.150"))

        def handle_message(x):
            self.logger.debug(("%s:%s" % x.address) + ' message received. message: %s.'%x.data)
            self.clients[x] = x.data

        def handle_connected(x):
            self.logger.debug(("%s:%s" % x.address) + ' connected. ')
            self.clients[x] = None
            self.timeouts[x] = time.time()

        def handle_close(x):
            if x in self.clients:
                del self.clients[x]
            self.logger.debug(("%s:%s"%x.address) + ' closed. ')

        self.socket_cls = type("SimpleSocket", (WebSocket, ), {
            "handleMessage":  handle_message,
            "handleConnected": handle_connected,
            "handleClose": handle_close,
        })

    def process_ws(self):
        while self.alive:
            try:
                for client, crawlid in self.clients.copy().items():
                    if crawlid:
                        record = self.rr.get_data(b"crawlid:%s"%crawlid.encode("utf-8"))
                        if record:
                            record["status"] = "finished" if self.rr.check_finish(
                                "crawlid:%s" % record.get("crawlid", "")) else "crawled"
                        if record.get("status") != "crawled":
                            self.logger.info("%s is finished. send back message and close the socket. "%crawlid)
                            client.sendMessage(json.dumps(record))
                            del self.timeouts[client]
                            del self.clients[client]
                            client.close()
                for client, t in self.timeouts.copy().items():
                    if t + self.settings.get("WEBSOCKET_TIMEOUT", 3600*24) < time.time():
                        self.logger.info("Socket timeout, closing...")
                        client.sendMessage(json.dumps({"error": True, "status": "finished"}))
                        del self.timeouts[client]
                        del self.clients[client]
                        client.close()
            except Exception:
                self.logger.error("Error in process_ws: %s"%traceback.format_exc())
            time.sleep(self.settings.get("WEBSOCKET_INTERVAL", 60))

    def start(self):
        self.th = Thread(target=self.process_ws)
        self.th.start()
        self.server = SimpleWebSocketServer(
            self.settings.get("HOST", ""), self.settings.get("WEBSOCKET_PORT", 8000), self.socket_cls)
        self.server.serveforever(self)
        self.server.close()

    def stop(self, *args):
        self.alive = False


if __name__ == "__main__":
    StatisticWebsocket().start()