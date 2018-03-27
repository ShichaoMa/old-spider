#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import sys
from argparse import ArgumentParser

from celery.__main__ import main

from utils import common_stop_start_control


def run():
    parser = ArgumentParser()
    parser.add_argument("-c", "--concurrency", help="Worker count. ", type=int)
    parser.add_argument("-rc", "--raw-cmd", help="Celery command. ", default="-A utils.tasks worker --loglevel=info")
    from settings import BASENAME, LOG_DIR, CONCURRENCY
    # 这个log是代替的标准输出和标准错误
    monitor_log_path = os.path.join(BASENAME, LOG_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")
    args = common_stop_start_control(parser, monitor_log_path, wait=2)

    if args.raw_cmd:
        args.raw_cmd += " --concurrency=%s" % CONCURRENCY
        cmd = args.raw_cmd.split()
        sys.argv[1:] = cmd
    main()


if __name__ == "__main__":
    run()
