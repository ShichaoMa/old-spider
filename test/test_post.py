# -*- coding:utf-8 -*-
import requests
# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
#     "Origin":"http://www.bluefly.com",
#     "Referer":"http://www.bluefly.com/balmain-balmain-mare-donna-women-open-toe-synthetic-black-gladiator-sandal/p/406816601",
#     "Host":"www.bluefly.com",
#     'Accept': 'application/json',
#     'Content-Type': 'application/json; charset=utf-8',
#     "Accept-Language": "en-US,en;q=0.5",
#
#     "Cookie": "_mzvr=vdXA6GkDbUmaDVFenkmbFA; mbdc=4807EE26.02E5.5654.9B0F.67EC86F251A0; _ibxep=1; __ibxl=1; sb-sf-at-prod-s=pt=&at=f4EJbd1+NZHxPyKVqLjFtHnujg4LTK8+aq/PmgRaZG5WizyWG0m6Dn4sZ9mCcy0OrFU1Ou887B86LKfM8nBkWDGcQWCiiltRW4GM9OucYT3PuTBPjaN/BC8m8o16MFNv5BJq5o3vINz87KJQt+CviaRgV2mSO0zLz2Kw1nEBg1YinKXHwsBE3E2Cb+ZPNWEGPlB0TmvHSJPaZjvgKNlBn+ZXFQVyuXdq7Ywk7NeIWIJM7Kb678rC7PRTtotYDxtIZnY84ZtCaRjrFe8O6kC6MqGhOpDc4uw3kuRuKdCUnPD6c2OTFWjvFL81Or/FqUsh&dt=2017-03-13T03:25:36.1671357Z; sb-sf-at-prod=pt=&at=f4EJbd1+NZHxPyKVqLjFtHnujg4LTK8+aq/PmgRaZG5WizyWG0m6Dn4sZ9mCcy0OrFU1Ou887B86LKfM8nBkWDGcQWCiiltRW4GM9OucYT3PuTBPjaN/BC8m8o16MFNv5BJq5o3vINz87KJQt+CviaRgV2mSO0zLz2Kw1nEBg1YinKXHwsBE3E2Cb+ZPNWEGPlB0TmvHSJPaZjvgKNlBn+ZXFQVyuXdq7Ywk7NeIWIJM7Kb678rC7PRTtotYDxtIZnY84ZtCaRjrFe8O6kC6MqGhOpDc4uw3kuRuKdCUnPD6c2OTFWjvFL81Or/FqUsh; _mzvs=yn; MOZU_AFFILIATE_IDS=%5B%5D; bounceClientVisit1447v=N4IgNgDiBcIBYBcEQKQGYCCKBMAxHuA7sQHQBGYArgKYBmYAniQMYD2AtgWQIZjvcBLAHYBaHn0Gj+AJ2oiAJqyFDuIwh2qjWETSISs5AZwZCEcaggHMxYbswDWIgOa35A7vukjD3IfN4EqHgALAAMAGwAHACM4eGh0SAANCDSMCAgAL5AA; _mzvt=C3mhRyT1Y0uwt7DroJ1q3A; mbcs=0B09AC0A-3C7E-5BB5-9B70-DB84B87C868A; viewedProducts=428927801,406816601; mozucartcount=%7B%223c9ed67a66f84c778642816d3fedcd3c%22%3A0%7D; _ga=GA1.2.92720157.1486958310; mbcc=3F04B8D9-B8D4-517B-BF3A-8503BCA14606",
#     "x-vol-app-claims": "K0Fb51pK4PRPjSvd71NmA30q4/fMpXDLG3J30DayPripsMFXRhZfH5K/AFT0AaztvwOtNOLmt2MEeF5Mw517ysS4C4o0QBqE/LcmhxbJ06JPtthzbnJ6Ur4zzo5KszUEJAEFl9aLIz18rwLtI1CG32hncfHPMRluWzNsjUlDS9kew1pHdEUd0yMbirHjcDovZD7qnatpYoHiIrnN2Pzv4OJC+w9AA+HrBb69fF2FOgr+nd4vPBpwCK6qcZi/boS0pBQ6vqnom8rwHgo+PHUAag==",
#     "x-vol-catalog":"1",
#     "Content-Length": "64",
#     "x-vol-currency":"USD",
#     "x-vol-locale":"en-US",
#     "x-vol-master-catalog":"1",
#     "x-vol-site": "16829",
#     "x-vol-tenant": "12106",
#     "x-vol-user-claims": "w1ezg+cksC5keYGzl4co5HSekYmX76OtmUNEDNguj5zjmW9Wg6BcskE/yXH5vfP9BkApAnVqagM22gJZiBsvMd+TmLLvRnbdwCAe7qCKtcnB7LLAuNEvjGs72pEgsbG1ykxdwWGGLupRODf/C3ey17xbfffkneScpBewFowzp5d8JWZM1uTNKvN7jV1NPeqJKxRuWQAaiu4zSNvoNiTmmrRX22AfvaI/xWXvvMw2ud/7PpD5ZJihYjqWHya/DC5czn/M3LrTTJ3eToVhBt3vVJROqpVk1infxxEqUgs9nKyOn3DUeZJKHLPgMgTFl/F729dwpILkZjRK6V0aUGNXs0wx9AnmMGpeA78tP9AEtUM=",
# }


HEADERS = {'Host': 'www.bluefly.com', 'Connection': 'keep-alive', 'Content-Length': '64', 'x-vol-master-catalog': '1', 'Origin': 'http://www.bluefly.com', 'x-vol-app-claims': '4Ed2A7XQFjmrtSrIIerOcUfDAQICUSJCV+TgtqKNX+TmLQbtxAtfCaHZQ/fHmCxor4oXFcb0mHGC52ma+M9sxrJR1X6korflTmxXLkVyLEnuVSh/sICFW/BH/TrqNkHkN+G0YA5pz7xF2BLf0k4BxCgFS+OTPSxOYhgw118iT0wmvbIwgyOOO/PyYrOZuVRjZ46TGaMrFl0Zr1NSaCiG1fgVbnC1Aj8FKitzlncv0xake+aqGxaYHZ+1SOkiWi3ibPUY7PzoQClnfTRREX/iAQ==', 'x-vol-currency': 'USD', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36', 'x-vol-site': '16829', 'Content-type': 'application/json', 'Accept': 'application/json', 'x-vol-user-claims': 'O8vuuNCJsBRHrYbnN+wI5ew4TuPCxKb4h0hggBlfOuXx2IHWyUN2c04ym93wmD4bIeQXzGymBbpn8A7GHoFlyhf4zhddXdn8tghRgJBu5cw2PR3b2YtgZ+X52wZEA4v48gROsv3K84WfOYDuP55AWZV0mUR/zaWLeVv9uzxM9GPOv52t0zl4MsVkfgCAiiAZKaFp9CjRYnMHoogulXc6Wc5rNt/YvhXJ95AmC10kquMg+jLm8LBYeSyVXVxUmWbIy/ZuXZLpvnp9G8EzyEI9V7NjmO7WEdRag8y0+M4Q9Ae4VjN3yjW1PLRgRGRN87MI4cga3ltjZSlQDZH3DI3NmAVOl7ejHzgv6Ix49NFWf5g=', 'x-vol-tenant': '12106', 'x-vol-locale': 'en-US', 'x-vol-catalog': '1', 'Referer': 'http://www.bluefly.com/balmain-balmain-mare-donna-women-open-toe-synthetic-black-gladiator-sandal/p/406816601', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8', 'Cookie': '_mzvr=vdXA6GkDbUmaDVFenkmbFA; mbdc=4807EE26.02E5.5654.9B0F.67EC86F251A0; _ibxep=1; __ibxl=1; sb-sf-at-prod-s=pt=&at=f4EJbd1+NZHxPyKVqLjFtHnujg4LTK8+aq/PmgRaZG5WizyWG0m6Dn4sZ9mCcy0OrFU1Ou887B86LKfM8nBkWDGcQWCiiltRW4GM9OucYT3PuTBPjaN/BC8m8o16MFNv5BJq5o3vINz87KJQt+CviaRgV2mSO0zLz2Kw1nEBg1YinKXHwsBE3E2Cb+ZPNWEGPlB0TmvHSJPaZjvgKNlBn+ZXFQVyuXdq7Ywk7NeIWIJM7Kb678rC7PRTtotYDxtIZnY84ZtCaRjrFe8O6kC6MqGhOpDc4uw3kuRuKdCUnPD6c2OTFWjvFL81Or/FqUsh&dt=2017-03-13T03:25:36.1671357Z; sb-sf-at-prod=pt=&at=f4EJbd1+NZHxPyKVqLjFtHnujg4LTK8+aq/PmgRaZG5WizyWG0m6Dn4sZ9mCcy0OrFU1Ou887B86LKfM8nBkWDGcQWCiiltRW4GM9OucYT3PuTBPjaN/BC8m8o16MFNv5BJq5o3vINz87KJQt+CviaRgV2mSO0zLz2Kw1nEBg1YinKXHwsBE3E2Cb+ZPNWEGPlB0TmvHSJPaZjvgKNlBn+ZXFQVyuXdq7Ywk7NeIWIJM7Kb678rC7PRTtotYDxtIZnY84ZtCaRjrFe8O6kC6MqGhOpDc4uw3kuRuKdCUnPD6c2OTFWjvFL81Or/FqUsh; _mzvs=yn; MOZU_AFFILIATE_IDS=%5B%5D; viewedProducts=428927801,406816601; mozucartcount=%7B%223c9ed67a66f84c778642816d3fedcd3c%22%3A0%7D; _ga=GA1.2.92720157.1486958310; mbcc=3F04B8D9-B8D4-517B-BF3A-8503BCA14606; _mzvt=8ShnugyNtkesMx8zTZDaUA'}

resp = requests.post(
    "http://www.bluefly.com/api/commerce/catalog/storefront/products/406816601/configure?includeOptionDetails=true&quantity=1",
    {"options":[{"attributeFQN":"tenant~shoes-size","value":"43987"}]}, headers=HEADERS)

print(resp.status_code)
import json
print(json.loads(resp.text))