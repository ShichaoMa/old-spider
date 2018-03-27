#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
from rancher_monitor import RancherMonitor, PROJECT


if __name__ == "__main__":
    rm = RancherMonitor()
    rm.set_logger()
    rm.run({"project": PROJECT, "service": "loco", "action": "restart"})
    rm.run({"project": PROJECT, "service": "amazon", "action": "restart"})
    rm.run({"project": PROJECT, "service": "offer", "action": "restart"})
    rm.run({"project": PROJECT, "service": "zappos", "action": "restart"})