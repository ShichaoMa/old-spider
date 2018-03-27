# -*- coding:utf-8 -*-
import copy
from http import cookiejar


class CookieJar(cookiejar.LWPCookieJar):

    def clear_except(self, *names):
        for domain, domain_cookie in copy.deepcopy(self._cookies).items():
            for path, path_cookie in domain_cookie.items():
                for name, value in path_cookie.items():
                    if name in names:
                        continue
                    else:
                        del self._cookies[domain][path][name]
