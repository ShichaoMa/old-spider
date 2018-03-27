# -*- coding:utf-8 -*-
from selenium.webdriver.common import proxy
from selenium.webdriver.firefox.remote_connection import FirefoxRemoteConnection

from selenium.webdriver.firefox.webdriver import WebDriver, DesiredCapabilities, RemoteWebDriver, FirefoxProfile

# myProxy = "http://192.168.200.51:8123"

# p = proxy.Proxy({
#     'proxyType': proxy.ProxyType.MANUAL,
#     'httpProxy': myProxy,
#     'ftpProxy': myProxy,
#     'sslProxy': myProxy,
#     'noProxy': '' # set this value as desired
#     })


def use_proxy():
    executor = FirefoxRemoteConnection(
                    remote_server_addr="http://127.0.0.1:4444")

    PROXY = "192.168.200.51:8123"

    capabilities = DesiredCapabilities.FIREFOX.copy()


    #
    # p = proxy.Proxy({
    # "httpProxy":PROXY,
    # "ftpProxy":PROXY,
    # "sslProxy":PROXY,
    # "noProxy":[],
    # "proxyType":"manual",
    # })

    del capabilities["marionette"]

    profile = FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", "192.168.200.51")
    profile.set_preference("network.proxy.socks_port", 1080)
    profile.update_preferences()

    # you have to use remote, otherwise you’ll have to code it yourself in python to
    driver =RemoteWebDriver(executor, capabilities, keep_alive=True, browser_profile=profile)

    #driver = WebDriver(proxy=p)
    driver.get("https://www.google.com/")


def direct():
    driver = WebDriver()
    driver.get("https://www.baidu.com/")


use_proxy()