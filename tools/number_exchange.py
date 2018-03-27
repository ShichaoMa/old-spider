# -*- coding:utf-8 -*-
from argparse import ArgumentParser


all_num = list("0123456789abcdefghijklmnopqrstuvwxyz")


def exchange(num, radix, result=""):
    if num:
        quotient, remainder = divmod(num, radix)
        return exchange(quotient, radix, result) + str(all_num[remainder])
    else:
        return ""


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-n", "--num", help="Number need to exchange. eg: 0x16")
    parser.add_argument("-r", "--radix", type=int, help="Radix used to exchange. eg: 4")
    args = parser.parse_args()
    if args.radix > len(all_num) or args.radix <= 1:
        raise Exception("非法进制: %s 2-%s"%(args.radix, len(all_num)))
    try:
        num = eval(args.num)
    except Exception:
        raise Exception("需要整型！")
    print(exchange(num, args.radix) or 0)