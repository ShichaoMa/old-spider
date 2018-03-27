# -*- coding:utf-8 -*-
from redis import Redis

r = Redis("192.168.200.150")

print(r.llen("convert_in_queue"))