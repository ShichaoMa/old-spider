#!/usr/bin/env python3.6
import os
import time
import json
import traceback

from redis import Redis
from toolkit import timeout, load_function
from toolkit.monitors import Service


class Worker(Service):

    def __init__(self):
        self.name = "image_filter_worker_%s" % os.getpid()
        super(Worker, self).__init__()
        self.convert_in_queue = self.args.in_queue
        self.convert_out_queue = self.args.out_queue
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get_int("REDIS_PORT"))
        self.convert_needs = ["images", "color_images", "crawlid", "spiderid", "product_id"]
        self.process_images = load_function("tasks.process_images")

    def start(self):
        while self.alive:
            message = self.redis_conn.rpop(self.convert_in_queue)
            if not message:
                time.sleep(1)
                continue
            item = json.loads(message)
            while self.alive:
                self.logger.debug("Start to send crawld: %s spiderid: %s product_id: %s to celery. "%(
                    item["crawlid"], item["spiderid"], item["product_id"]))
                t1 = time.time()
                try:
                    result = self.call_celery(item)
                except Exception:
                    self.logger.error("Unknow error: %s. " % traceback.format_exc())
                    continue
                if result:
                    self.logger.info("Celery task finished. crawld: %s spiderid: %s product_id: %s, "
                                     "result: %s call start time: %s, call end time %s, call "
                                     "duration: %s, process start time: %s, process end time %s, process duration %s. "%
                                     (item["crawlid"], item["spiderid"], item["product_id"],
                                     result.get("convert_result", True), t1, time.time(), time.time() - t1,
                                      result.get("start_process"), result.get("end_process"), result.get("cost")))
                    try:
                        self.redis_conn.lpush(self.convert_out_queue, json.dumps(result))
                    except Exception:
                        self.logger.error("Encode error: %s, item: %s"%(traceback.format_exc(), result))
                        item.pop("convert_failed_reason", None)
                        continue
                    break
                else:
                    self.logger.error("Celery timeout, rollback. ")
            else:
                self.logger.info("Process is been closed,  push back message: %s"%message)
                self.redis_conn.rpush(self.convert_in_queue, message)

    @timeout(500, False)
    def call_celery(self, item):
        msg = dict()
        for key, value in item.items():
            if key in self.convert_needs:
                msg[key] = value
        result = self.process_images.delay(msg)
        while not result.ready:
            time.sleep(.1)
        msg = result.get(propagate=False)
        if not isinstance(msg, dict):
            msg = dict(convert_failed_reason=msg)
            msg["convert_result"] = False
        item.update(msg)
        return item

    def enrich_parser_arguments(self):
        super(Worker, self).enrich_parser_arguments()
        self.parser.add_argument("-iq", "--in-queue")
        self.parser.add_argument("-oq", "--out-queue")


if __name__ == "__main__":
    Worker().start()
