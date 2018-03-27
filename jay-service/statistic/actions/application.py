# -*- coding:utf-8 -*-
import os

from bottle import static_file
from toolkit.monitors import LoggingMonitor

from ..utils import routing
from ..common import Common


class Application(LoggingMonitor, Common):
    """
        statistic app base.
    """
    settings = None
    logger = None
    name = "application"

    @routing(path="/static/<path:path:>")
    def static(self, path):
        return static_file(path, os.path.join(self.project_path, "static"))

    def close(self):
        pass
