# -*- coding:utf-8 -*-
CAPTCHA_FIELD = {
    "amazon": {
        "check": { # 用来检查是否出现了验证码，返回非空值为真
            "xpath": [
                '//title[@dir="ltr"]/text()',
            ],
            "function": lambda x, item: len(x.extract()) > 0 and (x.extract()[0] in ("Robot Check", "Amazon CAPTCHA", "Bot Check"))
        },
        "image": { # 用来获取验证码的图片链接
            "xpath": [
                '//div[@class="a-row a-text-center"]/img/@src',
            ],
            "function": lambda x, item: "".join(x.extract())
        },
        "captcha_form_url": { # 发送验证码结果的url
          "extract": lambda item, response: "/errors/validateCaptcha",
        },
        "key_value": { # 用来获取发送验证码时一并需要的参数 如参数为name=value，则通过xpath或者re获取的值列表应满足[name, value, name, value...]
            "xpath": [
                '//input[@type="hidden"]/@name|//input[@type="hidden"]/@value',
            ],
            "function": lambda x, item: x.extract(),
        },
    },
    "loco_amazon": {
        "check": { # 用来检查是否出现了验证码，返回非空值为真
            "xpath": [
                '//title[@dir="ltr"]/text()',
            ],
            "function": lambda x, item: len(x.extract()) > 0 and (x.extract()[0] in ("Robot Check", "Amazon CAPTCHA", "Bot Check"))
        },
        "image": { # 用来获取验证码的图片链接
            "xpath": [
                '//div[@class="a-row a-text-center"]/img/@src',
            ],
            "function": lambda x, item: "".join(x.extract())
        },
        "captcha_form_url": { # 发送验证码结果的url
          "extract": lambda item, response: "/errors/validateCaptcha",
        },
        "key_value": { # 用来获取发送验证码时一并需要的参数 如参数为name=value，则通过xpath或者re获取的值列表应满足[name, value, name, value...]
            "xpath": [
                '//input[@type="hidden"]/@name|//input[@type="hidden"]/@value',
            ],
            "function": lambda x, item: x.extract(),
        },
    },
}
