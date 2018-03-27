#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import sys
from argparse import ArgumentParser

from toolkit.daemon_ctl import common_stop_start_control
from toolkit.settings import SettingsWrapper
from toolkit.logger import Logger


def run():
    parser = ArgumentParser()
    parser.add_argument("-s", "--settings", default="settings.py")
    from settings import BASENAME, LOG_DIR
    # 这个log是代替的标准输出和标准错误
    monitor_log_path = os.path.join(BASENAME, LOG_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")
    args = common_stop_start_control(parser, monitor_log_path, wait=2)
    sw = SettingsWrapper()
    settings = sw.load(args.settings)
    logger = Logger.init_logger(settings, settings.get("PROJECT"))
    sys.path.insert(0, os.path.join(BASENAME, logger.name))
    from actions import Application
    Application.set_logger(logger, settings)
    Application.run()


if __name__ == "__main__":
    run()


