import os
import sys
import imp
import copy
import time
import logging
import datetime
import traceback
import importlib

from threading import Thread
from queue import Empty, Queue
from functools import wraps
from logging import handlers
from influxdb import InfluxDBClient
from pythonjsonlogger.jsonlogger import JsonFormatter


class SettingsWrapper(object):
    '''
    Wrapper for loading settings files and merging them with overrides
    '''

    my_settings = {}
    ignore = [
        '__builtins__',
        '__file__',
        '__package__',
        '__doc__',
        '__name__',
    ]

    def _init__(self):
        pass

    def load(self, local='localsettings.py', default='settings.py'):
        '''
        Load the settings dict

        @param local: The local settings filename to use
        @param default: The default settings module to read
        @return: A dict of the loaded settings
        '''
        self._load_defaults(default)
        self._load_custom(local)

        return self.settings()

    def load_from_string(self, settings_string='', module_name='customsettings'):
        '''
        Loads settings from a settings_string. Expects an escaped string like
        the following:
            "NAME=\'stuff\'\nTYPE=[\'item\']\n"

        @param settings_string: The string with your settings
        @return: A dict of loaded settings
        '''
        try:
            mod = imp.new_module(module_name)
            exec(settings_string in mod.__dict__)
        except TypeError:
            print("Could not import settings")
        self.my_settings = {}
        try:
            self.my_settings = self._convert_to_dict(mod)
        except ImportError:
            print("Settings unable to be loaded")

        return self.settings()

    def settings(self):
        '''
        Returns the current settings dictionary
        '''
        return self.my_settings

    def _load_defaults(self, default='settings.py'):
        '''
        Load the default settings
        '''
        if isinstance(default, str) and default[-3:] == '.py':
            default = default[:-3]

        self.my_settings = {}
        try:
            if isinstance(default, str):
                settings = importlib.import_module(default)
            else:
                settings = default
            self.my_settings = self._convert_to_dict(settings)
        except ImportError:
            print("No default settings found")

    def _load_custom(self, settings_name='localsettings.py'):
        '''
        Load the user defined settings, overriding the defaults

        '''
        if isinstance(settings_name, str) and settings_name[-3:] == '.py':
            settings_name = settings_name[:-3]

        new_settings = {}
        try:
            if isinstance(settings_name, str):
                settings = importlib.import_module(settings_name)
            else:
                settings = settings_name
            new_settings = self._convert_to_dict(settings)
        except ImportError:
            print("No override settings found")

        for key in new_settings:
            if key in self.my_settings:
                item = new_settings[key]
                if isinstance(item, dict) and \
                        isinstance(self.my_settings[key], dict):
                    for key2 in item:
                        self.my_settings[key][key2] = item[key2]
                else:
                    self.my_settings[key] = item
            else:
                self.my_settings[key] = new_settings[key]

    def _convert_to_dict(self, setting):
        '''
        Converts a settings file into a dictionary, ignoring python defaults

        @param setting: A loaded setting module
        '''
        the_dict = {}
        set = dir(setting)
        for key in set:
            if key in self.ignore:
                continue
            value = getattr(setting, key)
            the_dict[key] = value

        return the_dict


class UDPLogstashHandler(handlers.DatagramHandler):
    """Python logging handler for Logstash. Sends events over UDP.
    :param host: The host of the logstash server.
    :param port: The port of the logstash server (default 5959).
    :param message_type: The type of the message (default logstash).
    :param fqdn; Indicates whether to show fully qualified domain name or not (default False).
    :param version: version of logstash event schema (default is 0).
    :param tags: list of tags for a logger (default is None).
    """

    def makePickle(self, record):
        return self.formatter.format(record).encode("utf-8")


class Logger(object):
    """
    logger的实现
    """
    logger = None

    def __new__(cls, *args, **kwargs):
        # 保证单例
        if not cls.logger:
            cls.logger = super(Logger, cls).__new__(cls)
        return cls.logger

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    @classmethod
    def init_logger(cls, settings, name):
        json = settings.get_bool('LOG_JSON', True)
        level = settings.get('LOG_LEVEL', 'DEBUG')
        stdout = settings.get_bool('LOG_STDOUT', True)
        dir = settings.get('LOG_DIR', 'logs')
        bytes = settings.get('LOG_MAX_BYTES', '10MB')
        backups = settings.get_int('LOG_BACKUPS', 5)
        udp_host = settings.get("LOG_UDP_HOST", "192.168.200.132")
        udp_port = settings.get_int("LOG_UDP_PORT", 5230)
        file_out = settings.get_bool('LOG_FILE', False)
        logger = cls(name=name)
        logger.logger.propagate = False
        logger.json = json
        logger.name = name
        logger.format_string = '%(asctime)s [%(name)s]%(levelname)s: %(message)s'
        root = logging.getLogger()
        # 将的所有使用Logger模块生成的logger设置一样的logger level
        for log in root.manager.loggerDict.keys():
            root.getChild(log).setLevel(getattr(logging, level, 10))

        if stdout:
            logger.set_handler(logging.StreamHandler(sys.stdout))
        elif file_out:
            os.makedirs(dir, exist_ok=True)
            file_handler = handlers.RotatingFileHandler(
                os.path.join(dir, "%s.log"%name),
                maxBytes=bytes,
                backupCount=backups)
            logger.set_handler(file_handler)
        else:
            logger.set_handler(UDPLogstashHandler(udp_host, udp_port))

        return logger

    def set_handler(self, handler):
        handler.setLevel(logging.DEBUG)
        formatter = self._get_formatter(self.json)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.debug("Logging to %s"%handler.__class__.__name__)

    def __getattr__(self, item):
        if item.upper() in logging._nameToLevel:
            return extras_wrapper(self, item)(getattr(self.logger, item))
        raise AttributeError

    def _get_formatter(self, json):
        if json:
            return JsonFormatter()
        else:
            return logging.Formatter(self.format_string)

    def add_extras(self, dict, level):
        my_copy = copy.deepcopy(dict)
        if 'level' not in my_copy:
            my_copy['level'] = level
        if 'timestamp' not in my_copy:
            my_copy['timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if 'logger' not in my_copy:
            my_copy['logger'] = self.name
        return my_copy


def extras_wrapper(self, item):
    """
    logger的extra转用装饰器
    :param self:
    :param item:
    :return:
    """
    def logger_func_wrapper(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 2:
                extras = args[1]
            else:
                extras = kwargs.pop("extras", {})
            extras = self.add_extras(extras, item)
            return func(args[0], extra=extras)

        return wrapper

    return logger_func_wrapper


class InfluxDB(object):

    def __init__(self, influxdb_host, influxdb_port, influxdb_username, influxdb_password, influxdb_db):
        self.client = InfluxDBClient(influxdb_host, influxdb_port, influxdb_username, influxdb_password, influxdb_db)

    def write_points(self, table_name, tags, fields):
        try:
            self.client.write_points([{
                "measurement": table_name,
                "tags": tags,
                "time": datetime.datetime.utcnow(),
                "fields": fields
            }])
        except Exception:
            traceback.print_exc()


class InfluxDBDescriptor(object):

    def __init__(self, client):
        self.client = client

    def __get__(self, instance, owner):
        if not self.client:
            self.client = InfluxDB(
            )
        return self.client


def async_produce_wrapper(producer, logger):
    count = 0

    def wrapper(func):

        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            nonlocal count
            count += 1
            if count % 10 == 0:  # adjust this or bring lots of RAM ;)
                while True:
                    try:
                        msg, exc = producer.get_delivery_report(block=False)
                        if exc is not None:
                            logger.error('Failed to deliver msg {}: {}'.format(
                                msg.partition_key, repr(exc)))
                        else:
                            logger.debug('Successfully delivered msg {}'.format(
                                msg.partition_key))
                    except Empty:
                        break
            return result
        return inner
    return wrapper
