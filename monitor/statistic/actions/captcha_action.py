# -*- coding:utf-8 -*-
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from . import Application
from helper.common import routing


class Captcha(Application):
    """
        captcha action.
    """
    def __init__(self):
        self.captcha_url = 'http://www.jomashop.com/distil_verify'
        self.proxies = {"https": "http://%s" % self.settings.get("PROXY")}
        self.service_args = [
            '--proxy=%s' % self.settings.get("PROXY"),
            '--proxy-type=http'
        ]
        self.web = webdriver.PhantomJS(service_args=self.service_args)

    @routing(method=["GET", "POST"])
    def index(self):
        """
        验证码主页
        :return:
        """
        return self.render(self.index)

    @routing()
    def captcha(self):
        """
        使用selenium获取验证码
        :return:
        """
        try:
            self.logger.info("Start process captcha home page with proxy: %s. "%self.settings.get("PROXY"))
            self.web.get(self.captcha_url)
            time.sleep(10)
            img = self.web.find_element_by_id('recaptcha_challenge_image')
            v = self.web.find_element_by_xpath('//input[@name="V"]')
            v_val = v.get_attribute("value")
            self.response.set_cookie("v_val", v_val, path='/captcha/send')
            rm = self.web.find_element_by_xpath('//input[@name="RM"]')
            rm_val = rm.get_attribute("value")
            self.response.set_cookie("rm_val", rm_val, path='/captcha/send')
            img_url = img.get_attribute("src")
            self.response.set_cookie("img_url", img_url, path='/captcha/send')
            self.logger.debug("Captcha image url is %s. "%img_url)
            captcha_buf = img.screenshot_as_png
            self.logger.debug("Captcha process finished. ")
            return captcha_buf
        except Exception:
            self.logger.error("Error in captcha: %s. "%traceback.format_exc())

    @routing()
    def send(self):
        """
        验证码发送
        :return:
        """
        try:
            captcha = self.request.GET.get("captcha")
            self.logger.info("Captcha have recognized to %s. " % captcha)
            captcha_field = self.web.find_element_by_id("recaptcha_response_field")
            captcha_field.send_keys(captcha)
            captcha_field.send_keys(Keys.RETURN)
            page_size = len(self.web.page_source)
            self.logger.info("Send captcha to jomashop, result:%s, page_size: %s. " % (self.web.title, page_size))
            if page_size > 15000:
                self.logger.info("Captcha success. ")
                return {"success": True}
            return {"success": False}
        except Exception:
            self.logger.error("Error in send: %s. "%traceback.format_exc())
            return {"success": False}

    def close(self):
        try:
            self.web.close()
        except Exception:
            pass