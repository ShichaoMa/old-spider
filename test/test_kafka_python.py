from kafka import KafkaConsumer, KafkaProducer
from toolkit.manager import ExceptContext


def consume_(self, callback=lambda value: value, errorback=lambda message: message):
    with ExceptContext(ExceptContext, errback=self.log_err):
        with ExceptContext(StopIteration, errback=lambda *args: None):
            message = self.consumer.__next__()
            while message:
                value = message.value
                self.logger.debug('Consume message from %s, message is %s' % (self.topic_in, value))
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                value = callback(value)
                if value:
                    future = self.consumer.commit_async()
                    future.add_callback(self.callback)
                    future.add_errback(self.errback)
                    return value
                else:
                    message = errorback(message)

def errback(exception):
    print("Error in kafka feature: %s. " % str(exception))

def callback(value):
    print("Success in kafka feature: %s. " % value)

def consume():

    consumer = KafkaConsumer("jay_firehose_ingress", group_id="test",
              bootstrap_servers=["192.168.200.146:9092", "192.168.200.147:9092", "192.168.200.148:9092"],
              enable_auto_commit=False)

    for message in consumer:

        future = consumer.commit_async()
        future.add_callback(callback)
        future.add_errback(errback)
        import pdb
        pdb.set_trace()
        print(message)

def produce():
    producer = KafkaProducer(bootstrap_servers=["192.168.200.146:9092", "192.168.200.147:9092", "192.168.200.148:9092"])
    future = producer.send("jay_firehose_images", "test".encode("utf-8"))
    future.add_callback(lambda value: print(value))
    future.add_errback(lambda value: print(value))
    future.get(timeout=50)

produce()