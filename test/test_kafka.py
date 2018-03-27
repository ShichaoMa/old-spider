# -*- coding:utf-8 -*-
# from kafka import KafkaConsumer
# consumer = KafkaConsumer('jay_firehose_egress', bootstrap_servers=["192.168.200.141", "192.168.200.142", "192.168.200.143"], group_id="test")
#
# for i, k in enumerate(consumer):
#     print(i)

from pykafka import KafkaClient

client = KafkaClient(hosts="192.168.21.58:9092")

topic = client.topics[b"jay_firehose_ingress"]

balanced_consumer = topic.get_balanced_consumer(
    consumer_group=b'image_item_filter',
    auto_commit_enable=True,
    zookeeper_connect='192.168.21.58:2181',
    consumer_timeout_ms=1000
)

print(balanced_consumer.consume(False))
balanced_consumer.stop()


# for i, msg in enumerate(balanced_consumer):
#     print(i)


# from kafka import KafkaClient, SimpleConsumer
#
# client = KafkaClient("192.168.21.58")
# topic = "jay_firehose_ingress"
# comsumer = SimpleConsumer(client, "image_item_filter", "jay_firehose_ingress")
#
# print(comsumer.get_message())