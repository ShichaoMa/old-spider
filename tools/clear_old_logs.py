#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import os
import glob
import time
path = "/mnt/nas/logs"
refresh = 1


def main():
    print("Start to clean logs. ")
    files = [os.path.join(path, file) for file in glob.glob("%s/*"%path)]
    print("%s log files found. "%len(files))
    count = 0
    for file in files:
        stat = os.stat(file)
        days = (time.time() - stat.st_mtime) / (3600*24)
        if days > refresh:
            os.remove(file)
            count += 1
    print("Cleaning finished. %d log files was cleaned. "%count)

main()
