#!/usr/bin/env python3.6
import os
import re
import time
import subprocess

from redis import Redis
from bottle import static_file, route, request, run, redirect, template

redis_conn = Redis(os.environ.get("REDIS_HOST", "192.168.200.150"), int(os.environ.get("REDIS_PORT", 6379)))

process = None


@route("/")
def index():
    return template(os.path.join(os.path.dirname(__file__), "page.html"))


@route("/captcha")
def captcha():
    global process
    if not process:
        process = subprocess.Popen(["phantomjs",
                                    "--proxy=http://192.168.200.51:1080",
                                    "--proxy-type=socks5",
                                    os.path.join(os.path.dirname(__file__), "process_captcha.js")],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
    count = 0
    while not os.path.exists("captcha.png") and count < 20:
        time.sleep(1)
        count += 1
    if count >= 20:
        return {"error": "timeout"}
    else:
        return static_file("captcha.png", ".")


@route("/check")
def check():
    expire = redis_conn.hget("jomashop:cookies", "expire")
    return {"result": expire is None or expire.decode() == "True"}


@route("/rec")
def rec():
    global process
    try:
        if process:
            captcha = request.GET.get("captcha")
            process.stdin.write(captcha.encode() + b"\n")
            process.stdin.flush()
            os.unlink("captcha.png")
            buffer = process.stdout.read()
            cookies = re.search(r"Cookies is: (.*)", buffer.decode()).group(1)
            if cookies.strip():
                redis_conn.hmset("jomashop:cookies", {"cookies": cookies,
                                                      "refresh_timeline": time.time() + 100,
                                                      "expire": False})
        return redirect("/")
    finally:
        process = None


run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 12345)))
