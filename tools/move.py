# -*- coding:utf-8 -*-
import psycopg2
from redis import Redis
conn = psycopg2.connect("dbname='upc' user='roc_upc' host='127.0.0.1' password='roc_upc'")
redis_conn = Redis("192.168.200.90")
cur = conn.cursor()

# cur.execute("select roc_id from amazon_roc")
#
# for roc_id in cur:
#     print(roc_id)
#     redis_conn.sadd("roc_id_total_set", roc_id[0])

cur.execute("select upc from site_roc")

for upc in cur:
    print(upc)
    redis_conn.sadd("site_check_set", upc[0])
