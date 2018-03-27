#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import datetime
import traceback
from pymongo import MongoClient
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("--host", dest="host", default="192.168.200.120")
    parser.add_argument("-p", "--port", dest="port", type=int, default=27017)
    parser.add_argument("-d", "--days", dest="days", type=int, default=7)
    args = parser.parse_args()
    time = datetime.datetime.now()-datetime.timedelta(days=args.days)
    t_f = time.strftime("%Y%m%d%H%M%S")
    time = datetime.datetime.now() - datetime.timedelta(days=args.days-4)
    t_f_u = time.strftime("%Y%m%d%H%M%S")
    conn = None
    try:
        conn = MongoClient(args.host, args.port)
        print("connection created. ")
        db = conn.get_database("products")
        for collection in db.collection_names(include_system_collections=False):
            print("start to clean collection %s. "%collection)
            if collection == "jay_amazon_updates":
                rs = db[collection].delete_many({"timestamp":{"$lte":t_f_u}})
            else:
                rs = db[collection].delete_many({"timestamp":{"$lte":t_f}})
            print("collection %s have been removed %s record. "%(collection, rs.deleted_count))
    except Exception:
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()