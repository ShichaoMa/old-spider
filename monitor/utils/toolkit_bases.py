# -*- coding:utf-8 -*-
import random

from redis import Redis
from threading import RLock
from .core import Monitor
# from toolkit.mutil_monitor import MultiMonitor
# from toolkit.settings import SettingsWrapper
# from toolkit.logger import Logger
# import traceback
#
#
# class Monitor(MultiMonitor):
#     name = "monitor"
#     wrapper = SettingsWrapper()
#     _logger = None
#
#     def __init__(self, settings):
#         super(Monitor, self).__init__()
#         if isinstance(settings, dict):
#             self.settings = settings
#         else:
#             self.settings = self.wrapper.load(default=settings)
#
#     def set_logger(self, logger=None):
#         self._logger = logger
#
#     @property
#     def logger(self):
#         self._logger = self._logger or Logger.init_logger(self.settings, self.name)
#         return self._logger
#
#     def log_err(self, func_name, *args):
#         self.logger.error("Error in %s: %s. "%(func_name, "".join(traceback.format_exception(*args))))
#         return True


class ProxyPool(Monitor):
    """
        代理池
    """
    def __init__(self, settings):
        super(ProxyPool, self).__init__(settings)
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT", 6379))
        self.proxy_sets = self.settings.get("PROXY_SETS", "proxy_set").split(",")
        self.lock = RLock()
        self.proxy = {}

    def open(self):
        # 不使用Monitor基类关于多线程的操作方法
        pass

    def proxy_choice(self):
        """
        顺序循环选取代理
        :return: 代理
        """
        with self.lock:
            proxy = self.redis_conn.srandmember(random.choice(self.proxy_sets))
            if proxy:
                self.proxy = {"https": "http://%s@%s"%(self.settings.get("PROXY_ACCOUNT_PASSWORD"), proxy.decode("utf-8")),
                              "http": "http://%s@%s"%(self.settings.get("PROXY_ACCOUNT_PASSWORD"), proxy.decode("utf-8"))}
            return self.proxy


if __name__ == "__main__":
    import types
    #
    # mod = types.ModuleType("settings")
    # exec("REDID_HOST='192.168.200.150'", mod.__dict__)
    # print(ProxyPool(mod).proxy_choice())
