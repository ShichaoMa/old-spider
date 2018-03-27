import json
from kafka import KafkaConsumer


def main(bootstrap_servers, topic):
    consumer = KafkaConsumer(topic,
                             group_id='test',
                             #value_deserializer=lambda m: m and json.loads(m.decode('ascii')),
                             bootstrap_servers=bootstrap_servers)

    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                             message.offset, message.key,
                                             message.value))

if __name__ == "__main__":
    main(['192.168.200.146:9092', '192.168.200.147:9092', '192.168.200.148:9092'], 'csmpus_test')