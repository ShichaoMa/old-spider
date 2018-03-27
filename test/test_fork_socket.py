# -*- coding:utf-8 -*-
"""
测试fork中的socket不会因为主进程关闭而关闭
"""
import socket
import os
import signal


s = socket.socket()
s.bind(("0.0.0.0", 12346))
s.listen(10)
request, addr = s.accept()

def fun(*args):
    print(os.getpid())
    s.close()
signal.signal(signal.SIGINT, fun)
signal.signal(signal.SIGTERM, fun)
pid = os.fork()

if pid:
    request.close()
    print("parent close. ")
    import time
    time.sleep(30)
    print("Server wait connection")
    s.accept()
else:
    print("child recv", request.recv(1024))
    s.close()