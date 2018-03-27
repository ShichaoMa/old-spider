#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import sys
import requests
import datetime

index_prefixes = ["roc", "oct", "jay-logs", "jay-cluster", "taz"]

last = datetime.datetime.now() - datetime.timedelta(days=2)

for index in index_prefixes:
    resp = requests.delete("http://%s:9200/%s-%s"%(sys.argv[1], index, last.strftime("%Y.%m.%d")))
    print("Delete %s logs: %s"%(index, resp.status_code))