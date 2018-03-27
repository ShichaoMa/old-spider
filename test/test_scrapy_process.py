import requests

resp = requests.get("http://192.168.21.37/api/update", json={"urls": ["https://www.amazon.com/gp/product/B005WMH0YA/ref=twister_dp_update?ie=UTF8&psc=1"], "spiderid": "amazon", "extend": False})
print(resp.text)