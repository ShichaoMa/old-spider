# -*- coding:utf-8 -*-


class BaseComponent(object):

    def __init__(self, settings):
        print settings


class A(BaseComponent):

    def __init__(self):
        super(A, self).__init__(1111)

class D(A):

    def __init__(self):
        super(D, self).__init__()

class E(A):

    def __init__(self):
        super(E, self).__init__(4444, 5555)

class B(D):

    def __init__(self):
        super(B, self).__init__()

class C(E):
    def __init__(self):
        super(C, self).__init__()


class ItemProducer(B):

    def __init__(self, settings, topic_out):
        self.topic_out = topic_out
        print 22222, topic_out
        super(ItemProducer, self).__init__()


class ItemConsumer(C):
    name = "item_consumer"

    def __init__(self, settings, consumer, topic_in):
        super(ItemConsumer, self).__init__()


class ItemFilter(ItemConsumer, ItemProducer):

    def __init__(self, settings, consumer, topic_in, topic_out):

        ItemConsumer.__init__(self, settings, consumer, topic_in)
        ItemProducer.__init__(self, settings, topic_out)


class APAAItemFilter(ItemFilter):

    def __init__(self, settings):
        consumer = self.name
        topic_in = "jay.crawled_firehose_images"
        topic_out = "jay.crawled_firehose_apaa"
        super(APAAItemFilter, self).__init__(settings, consumer, topic_in, topic_out)


APAAItemFilter("aaaaaaa")

print APAAItemFilter.__mro__