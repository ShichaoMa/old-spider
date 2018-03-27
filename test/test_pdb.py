# -*- coding:utf-8 -*-
import pdb

def fun(e):
    print("this is in fun. ")
    gun(11)
    return e

def gun(d):
    print("this is in gun. ")
    bar(22)
    return d


def bar(c):
    print("this is in bar. ")
    pdb.set_trace()
    foo(33)
    return c

def foo(b):
    print("this is in foo. ")
    return b


def main(a):
    print("this is in main. ")
    fun(44)
    return a

if __name__ == "__main__":
    main(33)