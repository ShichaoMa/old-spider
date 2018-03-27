# -*- coding:utf-8 -*-
import json
import time
import traceback

from kafka import KafkaConsumer, KafkaProducer
from argparse import ArgumentParser
from abc import ABCMeta, abstractmethod

from toolkit import call_later
from toolkit.logger import Logger
from toolkit.mutil_monitor import MultiMonitor
from toolkit.settings import SettingsWrapper
from toolkit.manager import ExceptContext

from .helper import InfluxDBDescriptor


class Monitor(MultiMonitor):
    name = "monitor"
    wrapper = SettingsWrapper()
    _logger = None

    def __init__(self, settings):
        super(Monitor, self).__init__()
        if isinstance(settings, dict):
            self.settings = settings
        else:
            self.settings = self.wrapper.load(default=settings)

    def set_logger(self, logger=None):
        self._logger = logger

    @property
    def logger(self):
        self._logger = self._logger or Logger.init_logger(self.settings, self.name)
        return self._logger

    def log_err(self, func_name, *args):
        self.logger.error("Error in %s: %s. "%(func_name, "".join(traceback.format_exception(*args))))
        return True


class Component(Monitor):
    """
        Filter and Exporter bases.
    """
    name = "base_component"

    def __init__(self, **kwargs):
        super(Component, self).__init__(kwargs.pop("settings"))

    @classmethod
    def enrich_parser_arguments(cls, parser):
        parser.add_argument("-d", "--daemon", help="Run backend. ")
        parser.add_argument("-s", "--settings", help="Settings. ", default="settings.py")

    @classmethod
    def parse_args(cls):
        parser = ArgumentParser(conflict_handler="resolve")
        cls.enrich_parser_arguments(parser)
        data = vars(parser.parse_args())
        return cls(**data)


class ItemConsumer(Component):
    """
        Need kafka consumer.
    """
    name = "item_consumer"

    def __init__(self, **kwargs):
        super(ItemConsumer, self).__init__(**kwargs)
        self.topic_in = kwargs.pop("topic_in")
        self.consumer_id = kwargs.pop("consumer", self.name)
        self.consumer = None
        with ExceptContext(Exception, errback=lambda *args: self.stop()):
            self.consumer = KafkaConsumer(self.topic_in,
                                          group_id=self.consumer_id,
                                          bootstrap_servers=self.settings.get("KAFKA_HOSTS").split(","),
                                          enable_auto_commit=False,
                                          consumer_timeout_ms=1000)

    def consume_errback(self, exception):
        self.logger.error("Comsume feature failed: %s. " % str(exception))

    def consume_callback(self, value):
        self.logger.debug("Comsume feature success: %s. " % str(value))

    @call_later("commit", interval=10, immediately=False)
    def consume(self, callback=lambda value: value, errorback=lambda message: message):
        with ExceptContext(errback=self.log_err):
            with ExceptContext(StopIteration, errback=lambda *args: True):
                message = self.consumer.__next__()
                while message:
                    value = message.value
                    self.logger.debug('Consume message from %s, message is %s' % (self.topic_in, value))
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    value = callback(value)
                    if value:
                        return value
                    else:
                        message = errorback(message)

    def commit(self):
        future = self.consumer.commit_async()
        future.add_callback(self.consume_callback)
        future.add_errback(self.consume_errback)

    @classmethod
    def enrich_parser_arguments(cls, parser):
        Component.enrich_parser_arguments(parser)
        parser.add_argument("-ti", "--topic-in", help="Topic in. ")
        parser.add_argument("-c", "--consumer", help="consumer id. ")

    def stop(self, *args):
        super(ItemConsumer, self).stop(args)
        with ExceptContext(Exception, errback=lambda *args: True):
            if self.consumer:
                self.consumer.close()


class ItemProducer(Component):
    """
        Need kafka producer.
    """
    name = "item_producer"

    def __init__(self, **kwargs):
        super(ItemProducer, self).__init__(**kwargs)
        self.topic_out = kwargs.pop("topic_out")
        self.producer = None
        with ExceptContext(Exception, errback=lambda *args: self.stop()):
            self.producer = KafkaProducer(bootstrap_servers=self.settings['KAFKA_HOSTS'].split(","), retries=3)

    def produce_callback(self, value):
        self.logger.debug("Product future success: %s"%value)

    def produce_errback(self, value):
        self.logger.debug("Product future failed: %s" % value)

    def produce(self, message):
        with ExceptContext(Exception, errback=self.log_err):
            if not isinstance(message, list):
                message = [message]
            for msg in message:
                if isinstance(msg, str):
                    msg = msg.encode("utf-8")
                future = self.producer.send(self.topic_out, msg)
                future.add_callback(self.produce_callback)
                future.add_errback(self.produce_errback)
                future.get(timeout=50)

    @classmethod
    def enrich_parser_arguments(cls, parser):
        Component.enrich_parser_arguments(parser)
        parser.add_argument("-to", "--topic-out", help="Topic out. ")

    def stop(self, *args):
        super(ItemProducer, self).stop(args)


class ItemExporter(ItemConsumer, metaclass=ABCMeta):
    """
        Export base.
    """
    name = "item_exporter"

    def __init__(self, **kwargs):
        super(ItemExporter, self).__init__(**kwargs)

    def start(self):
        while self.alive:
            with ExceptContext(Exception, errback=self.log_err):
                message = self.consume()
                if message is None:
                    self.logger.debug("Haven't got message. ")
                    time.sleep(2)
                    continue
                self.logger.debug("Export message. ")
                self.export(message)

    @abstractmethod
    def export(self, message):
        pass


class ItemFilter(ItemConsumer, ItemProducer, metaclass=ABCMeta):
    """
        Filter base.
    """
    name = "item_filter"

    def __init__(self, **kwargs):
        super(ItemFilter, self).__init__(**kwargs)

    def start(self):
        while self.alive or [process for process in self.children if process.is_alive()]:
            with ExceptContext(errback=self.log_err):
                message = self.hook()
                if not message:
                    self.logger.debug("Haven't got hook message. ")
                    message = self.consume() if self.alive else None
                    if not message:
                        time.sleep(2)
                        continue
                    else:
                        self.logger.debug("Process message. ")
                        message = self.process_message(message)
                if not message:
                    self.logger.debug("Ignore produce message. ")
                    continue
                self.produce(message)

    def hook(self):
        pass

    @abstractmethod
    def process_message(self, message):
        pass

    @classmethod
    def enrich_parser_arguments(cls, parser):
        ItemConsumer.enrich_parser_arguments(parser)
        ItemProducer.enrich_parser_arguments(parser)
