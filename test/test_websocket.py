import os
import time
import json
import signal
from threading import Thread
from argparse import ArgumentParser

from log_to_kafka import Logger

from utils import common_stop_start_control
from utils.simple_websocket_server import SimpleWebSocketServer, WebSocket
from statistic.helper.store import RedisRepository


class StatisticWebsocket(Logger):
    is_alive = True

    def __init__(self, settings):
        super(StatisticWebsocket, self).__init__(settings)
        self.set_logger()
        self.open()
        self.clients = dict()
        self.rr = RedisRepository(self.settings.get("REDIS_HOST", "192.168.200.150"))
        that = self
        class SimpleClient(WebSocket):
            def handleMessage(self):
                that.clients[self] = self.data

            def handleConnected(self):
                that.clients[self] = None

            def handleClose(self):
                if self in that.clients:
                    del that.clients[self]
                self.logger.info(("%s:%s"%self.address) + 'closed. ')
        self.socket_cls = SimpleClient

    def process_ws(self):
        while self.is_alive:
            for client, crawlid in self.clients.copy().items():
                if crawlid:
                    record = self.rr.get_datas([crawlid])
                    record = record[0]
                    record["status"] = "finished" if self.rr.check_finish(
                        "crawlid:%s" % record.get("crawlid", "")) else "crawled"
                    if record["status"] == "finished":
                        client.sendMessage(json.dumps(record))
                        del self.clients[client]
                        client.close()
            time.sleep(1)

    def start(self):
        self.th = Thread(target=self.process_ws)
        self.th.start()
        self.server = SimpleWebSocketServer('', 8000, self.socket_cls)
        print(self.server.serversocket)
        self.server.serveforever(self)
        self.server.close()

    def stop(self, *args):
        self.is_alive = False

    def open(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    @classmethod
    def run(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", default="settings.py")
        from settings import BASENAME, LOG_DIR
        # 这个log是代替的标准输出和标准错误
        monitor_log_path = os.path.join(BASENAME, LOG_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")
        args = common_stop_start_control(parser, monitor_log_path, wait=10)
        cls(settings=args.settings).start()


if __name__ == "__main__":
    StatisticWebsocket.run()