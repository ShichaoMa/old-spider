# -*- coding:utf-8 -*-
import os

from bottle import static_file
from helper.common import Common, ActionMeta, routing


class Application(Common, metaclass=ActionMeta):
    """
        statistic app base.
    """
    @routing(path="/static/<path:path:>")
    def static(self, path):
        return static_file(path, os.path.join(self.project_path, "static"))