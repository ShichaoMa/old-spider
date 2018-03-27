#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import time
import signal
from subprocess import Popen
from argparse import ArgumentParser

from toolkit.daemon_ctl import common_stop_start_control

from utils.core import Monitor


class Controller(Monitor):
    """
        exporter和filter的总控制器
    """
    name = "controller"

    def start(self):
        """
        组建filter和exporter的命令，并通过shell的方式启动
        对死掉子进程进行重启， 统一关闭子进程
        :return:
        """
        processes = {}
        filters = self.settings.get("FILTERS")
        prefix = self.settings.get("TOPIC_PREFIX", "jay_firehose")
        ingress = self.settings.get("ENTER_NAME", "ingress")
        egress = self.settings.get("EXIT_NAME", "egress")
        for f, topics in filters:
            if not f.endswith(".py"):
                f += ".py"
            topic_in = "%s_%s"%(prefix, topics.get("in", ingress))
            topic_out = "%s_%s"%(prefix, topics.get("out", egress))
            consumer = topics.get("consumer")
            cmd = ("%s --topic-in %s --topic-out %s --consumer %s" %
                   (os.path.join(self.settings.get("BASENAME"), f),
                    topic_in, topic_out, consumer)).split(" ")
            processes[tuple(cmd)] = Popen(cmd)

        exporter = self.settings.get("EXPORTER")
        if not exporter.endswith(".py"):
            exporter += ".py"
        cmd = ("%s --topic-in %s --consumer %s" %
               (os.path.join(self.settings.get("BASENAME"), exporter),
                             "%s_%s"%(prefix, egress), self.settings.get("EXPORTER_CONSUMER"))).split(" ")

        processes[tuple(cmd)] = Popen(cmd)

        while self.alive:
            for cmd, process in processes.items():
                if process.poll() is None:
                    continue
                else:
                    self.logger.info("Process %s is dead restart again. "%cmd[0])
                    processes[cmd] = Popen(cmd)
            time.sleep(1)

        self.logger.info("Close all processes. ")

        for cmd, process in processes.items():
            self.logger.info("Send signal to %s. "%(' '.join(cmd)))
            process.send_signal(signal.SIGTERM)

        while True:
            ps = dict([(k, v) for k, v in processes.items() if v.poll() is None])
            if not ps:
                break
            self.logger.info("Wait for processes %s close. "%ps)
            time.sleep(1)

    def stop(self, *args):
        self.alive = False

    @classmethod
    def run(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", default="settings.py")
        from settings import BASENAME, LOG_DIR
        # 这个log是代替的标准输出和标准错误
        monitor_log_path = os.path.join(BASENAME, LOG_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")
        args = common_stop_start_control(parser, monitor_log_path, wait=10)
        controller = cls(settings=args.settings)
        controller.set_logger()
        controller.start()


if __name__ == "__main__":
    Controller.run()