import requests

print(requests.get("http://www.amazon.com/", proxies={"https": "http://60.2.148.253:80"}).status_code)