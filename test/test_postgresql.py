# -*- coding:utf-8 -*-
import psycopg2

def main():
    conn = psycopg2.connect("dbname='stella_production' user='star' host='192.168.200.80' password='star'")
    cur = conn.cursor()
    cur.execute("select account, name from users;")
    data = cur.fetchall()
    new_dic = dict()
    for account, name in data:
        new_dic.setdefault(name.strip(), []).append(account)
    for name in new_dic.keys():
        print(name, new_dic[name])
        if len(new_dic[name]) > 1:
            if new_dic[name][0].isdigit():
                cur.execute("delete from users where account='%s';" % new_dic[name][0])
                cur.execute(
                    "update from users set account='%s' where account='%s';" % (new_dic[name][0], new_dic[name][1]))
            else:
                cur.execute("delete from users where account='%s';" % new_dic[name][1])
                cur.execute(
                    "update from users set account='%s' where account='%s';" % (new_dic[name][1], new_dic[name][0]))
        # else:
        #     if new_dic[name][0].isalpha():
        #         cur.execute(
        #             "update from users set account='%s' where account='%s';" % (, new_dic[name][0]))


if __name__ == "__main__":
    main()