#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
    使用curl -k https://dnsapi.cn/Record.List -d "login_email=lihaili1987@163.com&login_password=meiguogou5.com&domain_id=45174230"
    获取 recode_id
"""
import time
import urllib
import socket
import httplib


params = dict(
    login_email="lihaili1987@163.com", # replace with your email
    login_password="meiguogou5.com", # replace with your password
    format="json",
    domain_id=45174230, # replace with your domain_od, can get it by API Domain.List
    record_id=224938391, # replace with your record_id, can get it by API Record.List
    sub_domain="abc", # replace with your sub_domain
    record_line="默认",
)
current_ip = None


def ddns(ip):
    params.update(dict(value=ip))
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
    conn = httplib.HTTPSConnection("dnsapi.cn")
    conn.request("POST", "/Record.Ddns", urllib.urlencode(params), headers)
    
    response = conn.getresponse()
    print(response.status, response.reason)
    data = response.read()
    print(data)
    conn.close()
    return response.status == 200


def getip():
    sock = socket.create_connection(('ns1.dnspod.net', 6666))
    ip = sock.recv(16)
    sock.close()
    return ip


if __name__ == '__main__':
    while True:
        try:
            ip = getip()
            print(ip)
            if current_ip != ip:
                if ddns(ip):
                    current_ip = ip
        except Exception as e:
            print(e)
        time.sleep(30)
