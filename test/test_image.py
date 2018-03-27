from monitor.utils.image_process import ImageProcess
from pymongo import MongoClient
mc = MongoClient("192.168.200.120")
db = mc["products"]["jay_victoriassecrets"]

cur = db.find({"crawlid": "201610240006"})
document = cur.next()
ip = ImageProcess("monitor.settings.py")
import logging
logger = logging.getLogger()
import sys
logger.setLevel(10)
logger.addHandler(logging.StreamHandler(sys.stdout))
ip.set_logger(logger)
spider = "victoriassecret"
re = ip.process_image(spider, document)
for image in document["images"]:
    if "bytesio" in image:
        image["bytesio"] = None
    print(image)
