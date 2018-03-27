#!/usr/bin/env python3.6
import os
import json
import time
import traceback

from queue import Empty
from threading import RLock
from bottle import run, route, request
from multiprocessing import Process, Queue

from scrapy.http import Request
from scrapy.signals import item_scraped
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from toolkit import load_class
from toolkit.managers import ExceptContext


settings = get_project_settings()
logger = load_class("crawling.utils.CustomLogger").init_logger(settings, "scrapy_process")
lock = RLock()


def crawl(item_scraped_handler, urls, **kwargs):
    settings["SCHEDULER"] = 'crawling.scheduler.SingleTaskScheduler'
    settings["ITEM_PIPELINES"] = {}
    settings["IDLE"] = False
    process = CrawlerProcess(settings)

    def start_requests():
        return [Request(url=url, meta=kwargs, callback=kwargs.get("callback", "parse_item"),
                        errback="errback") for url in urls]

    process.crawl(kwargs.get("spiderid"), start_requests=start_requests)
    for crawler in process.crawlers:
        crawler.signals.connect(item_scraped_handler, signal=item_scraped)
    process.start()


@route("/")
def hello():
    return_value = {}
    with lock:
        with ExceptContext(errback=lambda _, *args: logger.error("Error: %s"%traceback.format_exception(*args)) is None,
                           finalback=lambda got_err: return_value.__setitem__("error", return_value.get("error") or got_err)):
            urls = request.json.pop("urls")
            meta = {
                "crawlid": request.json.get("crawlid", time.strftime("%Y%m%d%H%M%S")),
                "spiderid": request.json["spiderid"],
                "priority": 1,
            }
            meta.update(request.json)
            if urls:
                logger.info("Get urls : %s" % urls)
                queue = Queue()

                def item_scraped_handler(**kwargs):
                    queue.put_nowait(kwargs.pop("item"))

                process = Process(target=crawl, args=(item_scraped_handler, urls), kwargs=meta)
                logger.debug("Process in scrapy")
                process.start()
                process.join(60)
                items = []
                while True:
                    try:
                        items.append(queue.get_nowait())
                    except Empty:
                        break
                logger.debug("Scrape finished got %s items"%len(items))
                process.terminate()
                return_value["data"] = json.loads(json.dumps(items, cls=load_class("crawling.utils.ItemEncoder")))
            else:
                return_value["error"] = "miss urls"
    return return_value


if __name__ == "__main__":
    run(host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", 8888))