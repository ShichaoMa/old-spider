import time
import pickle
import json
from redis import Redis

from pykafka import KafkaClient


def produce(message):
    kafka_client = KafkaClient("192.168.200.141:9092,192.168.200.142:9092,192.168.200.143:9092")
    producer = kafka_client.topics[b"roc_ingester_event"].get_producer(delivery_reports=True)
    producer.produce(json.dumps(message).encode("utf-8"))
    producer.stop()


if __name__ == "__main__":
    produce({'data': {'created_at': '2017-06-26 11:49:19',
  'fingerprint': 'e8acc509849ada701bf887738d8a5ffaf86ffab2',
  'roc_id': 'AMZN#B00K1VXG22',
  'source_site_code': 'AMZN',
  'updated_at': '2017-09-10 06:43:34',
  'url': 'https://www.amazon.com/Calvin-Klein-Chronograph-Watch-K5A27141/dp/B00K1VXG22/ref=sr_1_40/145-0364548-4484536?s=apparel&ie=UTF8&qid=1500625087&sr=1-40&nodeID=6358540011&psd=1&refinements=p_n_feature_browse-bin%3A379305011%2Cp_89%3ACalvin+Klein'},
 'data_type': 'parent_ware',
  'delay_date': time.time() * 1000,
 'event': 'created',
 'source_site_code': 'AMZN',
 'timestamp': '2017-09-10 06:43:34'})