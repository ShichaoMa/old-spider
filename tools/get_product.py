# -*- coding:utf-8 -*-
import time
import traceback
from psycopg2 import connect, IntegrityError
from pymongo import MongoClient
import json
import requests

from redis import Redis
from scrapy import Selector
from queue import Queue, Empty
from threading import Thread, RLock
from log_to_kafka import Logger
from multi_thread_closing import MultiThreadClosing

import hmac
import time
import base64
import hashlib

from urllib.parse import quote

AWSAccessKeyId = 'AKIAJXVX54GCJP4AO4AQ'
AWSSecretKey = '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'
AssociateTag = 'zdbnm06-20'


def aws_signed_request(region, params, public_key=AWSAccessKeyId, private_key=AWSSecretKey, associate_tag=AssociateTag,
                       version='2011-08-01'):
    """
    Copyright (c) 2010-2012 Ulrich Mierendorff

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
    """

    """
    Parameters:
        region - the Amazon(r) region (ca,com,co.uk,de,fr,co.jp)
        params - a dictionary of parameters, for example
                    {'Operation': 'ItemLookup',
                     'ItemId': 'B000X9FLKM',
                     'ResponseGroup': 'Small'}
        public_key - your "Access Key ID"
        private_key - your "Secret Access Key"
        version [optional]
    """

    # some paramters
    method = 'GET'
    host = 'webservices.amazon.' + region
    uri = '/onca/xml'

    # additional parameters
    params['Service'] = 'AWSECommerceService'
    params['AWSAccessKeyId'] = public_key
    params['Timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    params['Version'] = version
    if associate_tag:
        params['AssociateTag'] = associate_tag

    # create the canonicalized query
    canonicalized_query = [quote(param).replace('%7E', '~') + '=' + quote(params[param]).replace('%7E', '~')
                           for param in sorted(params.keys())]
    canonicalized_query = '&'.join(canonicalized_query)

    # create the string to sign
    string_to_sign = method + '\n' + host + '\n' + uri + '\n' + canonicalized_query

    # calculate HMAC with SHA256 and base64-encoding
    if isinstance(private_key, str):
        private_key = private_key.encode("utf-8")
    if isinstance(string_to_sign, str):
        string_to_sign = string_to_sign.encode("utf-8")
    signature = base64.b64encode(hmac.new(key=private_key, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    if isinstance(signature, bytes):
        signature = signature.decode("utf-8")
    # encode the signature for the request
    signature = quote(signature).replace('%7E', '~')

    return 'http://' + host + uri + '?' + canonicalized_query + '&Signature=' + signature


class GetProdcuts(Logger, MultiThreadClosing):
    """
        使用amazon webservice api进行ean mpn upc等信息获取
    """
    name = "apaa_item_filter"

    def __init__(self, **kwargs):
        super(GetProdcuts, self).__init__(**kwargs)
        self.redis_conn = Redis("192.168.200.94")
        self.conn_mongo = MongoClient("192.168.200.120")
        self.col = self.conn_mongo["products"]["jay_amazon_updates"]
        self.conn_tem = connect("dbname='upc' user='roc' host='127.0.0.1' password='roc'")
        self.cursor_tem = self.conn_tem.cursor()
        self.lock = RLock()
        self.queue = Queue()
        self.set_logger()
        self.open()

    def start(self):
        for apaa_thread in range(self.settings.get("APAA_THREADS", 1)):
            thread = Thread(target=self.process_apaa)
            self.threads.append(thread)
            thread.start()
        rs = self.col.find({}, {"asin": 1, "parent_asin": 1})
        next = rs.next()
        while next and self.alive:
            if next["asin"].startswith("joma"):
                next = rs.next()
                continue
            roc_id = "AMZN#%s#%s"%(next["parent_asin"], next["asin"])
            if not self.redis_conn.sismember("roc_id_total_set", roc_id):
                self.queue.put(next)
            next = rs.next()

    def process_apaa(self):
        """
        发送apaa请求子线程，队列中的消息数大于10时，统一发送一次webservice请求
        """
        items = []
        while self.alive:
            self.lock.acquire()
            if not items and self.queue.qsize() > 10:
                for i in range(10):
                    try:
                        items.append(self.queue.get_nowait())
                    except Empty:
                        break
            self.lock.release()
            if items:
                try:
                    asins = [i["asin"] for i in items]
                    self.logger.debug("Apaa request: %d, %s. " % (len(asins), asins))
                    url = aws_signed_request('com', {
                        'Operation': 'ItemLookup',
                        'ItemId': ','.join(asins),
                        'ResponseGroup': 'ItemAttributes'})
                    resp = requests.get(url, timeout=10)
                    self.logger.info("Apaa response code: %s. " % resp.status_code)
                    if resp.status_code == 200:
                        partial_items = dict((x["asin"], x) for x in items)

                        for code in ["upc", "ean", "mpn"]:
                            lst = Selector(text=resp.text).xpath(
                                '//%s/text()|//%s/../../asin/text()' % (code, code)).extract()
                            for i in range(0, len(lst), 2):
                                item = partial_items.get(lst[i])
                                item[code] = lst[i + 1]
                        for item in partial_items.values():
                            roc_id = "AMZN#%s#%s" % (item["parent_asin"], item["asin"])
                            try:
                                self.cursor_tem.execute("insert into AMAZON_ROC values (%s, %s, %s, %s, %s);", (
                                    roc_id, item["asin"], item.get("upc", ""), item.get("ean", ""), item.get("mpn", "")))
                                self.conn_tem.commit()
                            except IntegrityError:
                                self.conn_tem.rollback()
                                traceback.print_exc()
                            self.redis_conn.sadd("roc_id_total_set", roc_id)
                        items = []
                    else:
                        self.logger.error("API process failed. retry. ")
                        time.sleep(1)
                except Exception:
                    self.logger.error("Error in process_apaa: %s. "%traceback.format_exc())
                    self.conn_tem.rollback()
            else:
                time.sleep(1)


if __name__ == "__main__":
    GetProdcuts().start()
