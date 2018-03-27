#!/usr/bin/env python3.6
# -*- coding:utf-8 -*-
import os
import time
import signal
from subprocess import Popen

from toolkit.monitors import Service


class Controller(Service):
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
                   (os.path.join(".", f),
                    topic_in, topic_out, consumer)).split(" ")
            processes[tuple(cmd)] = Popen(cmd)

        exporter = self.settings.get("EXPORTER")
        if not exporter.endswith(".py"):
            exporter += ".py"
        cmd = ("%s --topic-in %s --consumer %s" %
               (os.path.join(".", exporter),
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


if __name__ == "__main__":
    Controller().start()
