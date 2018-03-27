# -*- coding:utf-8 -*-
import os
import sys
from subprocess import call
from functools import partial
from argparse import ArgumentParser

call = partial(call, stderr=sys.stdout, stdout=sys.stdout)

cmds = [
    "docker build -f docker/%s.dockerfile -t 192.168.200.51/longen/jay-%s:latest .",
    "docker push 192.168.200.51/longen/jay-%s"
    ]


def main():
    parser = ArgumentParser()
    parser.add_argument("-m", "--message", default="auto commit")
    parser.add_argument("services", nargs="+", help="service")
    args = parser.parse_args()
    result = True
    for service in args.services:
        result = result and deploy(service)
        if not result:
            return
    if result:
        call(["git", "commit", "-a", "-m", args.message])
        call(["git", "push"])


def deploy(service):
    if os.path.exists("jay-%s/%s.dockerfile.custom"%(service, service)):
        combine(service)
        return _deploy(service)
    else:
        print("Cannot find %s dockerfile! "%service)
        return False


def _deploy(service):
    for cmd in cmds:
        if call((cmd%tuple([service]*cmd.count("%s"))).split(" ")):
            return False
    return True


def combine(service):
    with open("docker/%s.dockerfile"%service, "w") as f:
        f.write(open("docker/dockerfile.base").read())
        f.write(open("jay-%s/%s.dockerfile.custom"%(service, service)).read())


if __name__ == "__main__":
    main()
