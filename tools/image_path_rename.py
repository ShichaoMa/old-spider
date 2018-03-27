# -*- coding:utf-8 -*-
import psycopg2

conn = psycopg2.connect(database="roc_production", user="postgres", password="postgres", host="192.168.200.152", port="5432")

cursor = conn.cursor()

import pdb
pdb.set_trace()
print("Success")

