# coding:utf-8

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

browser = webdriver.Firefox()
browser.get('http://www.baidu.com/')

assert u"百度一下" in browser.title
elem = browser.find_element_by_name("wd")
elem.send_keys(u"你好，Python")
elem.send_keys(Keys.RETURN)
source = browser.page_source
source = source.encode('gb2312','ignore')

print source


print browser.get_cookies()