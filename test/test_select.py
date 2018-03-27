import select
import time
import socket
from threading import Thread

client = socket.socket()

client.connect(("", 12312))

def fun():
    while True:
        f = open("test_selenium.py", "rb")
        fs, _, _ = select.select([f], [], [], 0.1)
        print(fs)
        f.close()
        time.sleep(1)

Thread(target=fun).start()


clients, _, a = select.select([client], [], [], 20)

import pdb
pdb.set_trace()

print(clients.recv(1024))

print("finished")

