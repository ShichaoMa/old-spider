#!/usr/bin/env python3.6
from argparse import ArgumentParser

from toolkit.logger import Logger
from toolkit.settings import SettingsWrapper
from toolkit import load_function as load_class
from toolkit.daemon_ctl import common_stop_start_control


def run():
    parser = ArgumentParser()
    parser.add_argument("-s", "--settings", default="settings.py")
    args = common_stop_start_control(parser, "/dev/null", wait=2)
    sw = SettingsWrapper()
    settings = sw.load(args.settings)
    logger = Logger.init_logger(settings, "statistic")
    Application = load_class("statistic.actions.Application")
    Application.set_logger(logger, settings)
    Application.run()


if __name__ == "__main__":
    run()


