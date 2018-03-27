#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import sys

from celery.__main__ import main
from argparse import ArgumentParser
from toolkit.daemon_ctl import common_stop_start_control


def run():
    parser = ArgumentParser()
    parser.add_argument("-c", "--concurrency", help="Worker count. ", type=int, default=1)
    parser.add_argument("-rc", "--raw-cmd", help="Celery command. ", default="-A tasks worker --loglevel=info")
    args = common_stop_start_control(parser, "/dev/null", wait=2)
    if args.raw_cmd:
        args.raw_cmd += " --concurrency=%s" % os.environ.get("CONCURRENCY", args.concurrency)
        cmd = args.raw_cmd.split()
        sys.argv[1:] = cmd
    main()


if __name__ == "__main__":
    run()
