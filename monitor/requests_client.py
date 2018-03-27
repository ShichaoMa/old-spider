#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import sys
import json
import signal
import socket
import requests

from argparse import ArgumentParser

from multi_thread_closing import MultiThreadClosing


class RequestsClient(MultiThreadClosing):

    def start(self):
        parser = ArgumentParser()
        parser.add_argument("--port", type=int, required=True)
        args = parser.parse_args()
        server = socket.socket()
        server.bind(("", args.port))
        server.listen(0)
        client, addr = server.accept()
        while self.alive:
            buffer = client.recv(10240)
            if not buffer:
                break
            meta = json.loads(buffer)
            resp = requests.get(meta.get("url"), headers=meta.get("headers"), proxies=meta.get("proxies"), timeout=meta.get("timeout"), stream=True)
            for chunk in resp.iter_content(10240):
                client.send(chunk)
            client.send(("\n%d\nabcdefghijklmn"%resp.status_code).encode())


if __name__ == "__main__":
    rc = RequestsClient()
    rc.set_logger()
    rc.start()