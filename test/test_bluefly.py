import requests
import json


headers = dict(x.split(":", 1) for x in """User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36
x-vol-app-claims:dT4DuhD38QDBERWJshp5PASjtQ50Xp2Y+TYSCkuLmdFqL6E0BlRPtlgJVeI+wn6NGO0wy9pPpPK5vq0bKUEaiBZFmGY/8W5S8E4btcVdN51ofDJzF4IcQQBbwJBnd5cg4EQCVLxBY0wExcQothHS15F1Cureeu4F73Nl6JS6+gB3MaBDiK8VmEk9nLlueb+rHjU1puKpOAdKaVJ4f0b36dUi69HL8ctYad09dTdEOSliH6HXhFlDNFFX5PRRoSmkAD4pu+TH6BFuDewmxqaMtg==
x-vol-user-claims:u8hvIm3nvGWnvngfvkJTSRnhCTFClftWgfVhT3zBGCGKx9egbbboMACRehCF0hu/RAI48Qf/JMF/dfMvVE89FlHYL+HF/e915q7XyvMfSr5C33FYbOlYcqPeyUR0LD5739/35bz+51Opn0DzODVcN3VVWHqYhYMHjKzN50Bf5D2db3N04lGDegb7M14VIgnZpt/FBzoT2FAb81O7OeVga3kWsYfgAkEBGnBRAruTJ1QgCI4XbIoEwacFgvuNd/kTQyEalHZPMBi34l00xG2QQxW/xfBANur2jp15/mS+hFtj1q+Amn3MIwBnLUJDpYtnQTsMDrD8Td/Uc2WCF0xmVDyYjGff9TOnyY/yEfUjS7g=""".split("\n"))


headers = dict(map(lambda x: (x[0].decode("utf-8"), b"".join(x[1]).decode("utf-8")), {b'Referer': [b'http://www.bluefly.com/dc-shoes-dc-shoes-anvil-nb-round-toe-leather-skate-shoe/p/432831901'], b'Accept': [b'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'], b'Accept-Language': [b'en'], b'User-Agent': [b'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'], b'Cookie': [b'_mzvr=xFGl9GmYLkuh7h_Sb1_w_g; _mzvs=nn; _mzvt=3zgmueKFYk6tuetN76lzBA'], b'Content-Length': [b'0'], b'X-Vol-App-Claims': [b'dT4DuhD38QDBERWJshp5PASjtQ50Xp2Y+TYSCkuLmdFqL6E0BlRPtlgJVeI+wn6NGO0wy9pPpPK5vq0bKUEaiBZFmGY/8W5S8E4btcVdN51ofDJzF4IcQQBbwJBnd5cg4EQCVLxBY0wExcQothHS15F1Cureeu4F73Nl6JS6+gB3MaBDiK8VmEk9nLlueb+rHjU1puKpOAdKaVJ4f0b36dUi69HL8ctYad09dTdEOSliH6HXhFlDNFFX5PRRoSmkAD4pu+TH6BFuDewmxqaMtg=='], b'X-Vol-User-Claims': [b'u8hvIm3nvGWnvngfvkJTSRnhCTFClftWgfVhT3zBGCGKx9egbbboMACRehCF0hu/RAI48Qf/JMF/dfMvVE89FlHYL+HF/e915q7XyvMfSr5C33FYbOlYcqPeyUR0LD5739/35bz+51Opn0DzODVcN3VVWHqYhYMHjKzN50Bf5D2db3N04lGDegb7M14VIgnZpt/FBzoT2FAb81O7OeVga3kWsYfgAkEBGnBRAruTJ1QgCI4XbIoEwacFgvuNd/kTQyEalHZPMBi34l00xG2QQxW/xfBANur2jp15/mS+hFtj1q+Amn3MIwBnLUJDpYtnQTsMDrD8Td/Uc2WCF0xmVDyYjGff9TOnyY/yEfUjS7g='], b'Accept-Encoding': [b'gzip,deflate']}.items()))
print(11111111, headers)
payloads = {"options":[{"attributeFQN":"tenant~mens-shoes-size","value":43987}]}


url = "http://www.bluefly.com/api/commerce/catalog/storefront/products/431294901/configure?includeOptionDetails=true&quantity=1"

resp = requests.post(url, json=payloads, headers=headers)

data = json.loads(resp.content)

print(resp.status_code)

#print(data["price"]["price"])

refresh_url = "http://www.bluefly.com/token/refresh"

resp = requests.post(refresh_url, headers=headers)

print(resp.status_code)

print(resp.headers)

headers["x-vol-app-claims"] =  resp.headers["x-vol-app-claims"]

headers["x-vol-user-claims"] =  resp.headers["x-vol-user-claims"]

resp = requests.post(url, json=payloads, headers=headers)

data = json.loads(resp.content)

print(resp.status_code)

print(data)

