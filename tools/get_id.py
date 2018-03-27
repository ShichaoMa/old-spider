from argparse import ArgumentParser
from psycopg2 import connect
from os.path import basename, splitext


def main():
    parser = ArgumentParser()
    parser.add_argument("-cp", "--conf-path", required=True, help="config path. If config path name is brands.conf,"
                                                                  " then `brands` will deliver to tuple_ele. ")
    parser.add_argument("-te", "--tuple-ele")
    args = parser.parse_args()
    with open(args.conf_path) as f:
        mapping = dict(reversed(line.strip().split(",")) for line in f.readlines() if line.strip())
    conn = connect("dbname='roc_production' user='postgres' host='192.168.200.152' password='postgres'")
    cursor = conn.cursor()
    table_name = args.tuple_ele or splitext(basename(args.conf_path))[0]
    cursor.execute("SELECT id, code FROM %s;"%table_name)
    elements = cursor.fetchall()
    new_mapping = dict()
    #ele = dict()
    for id, code in elements:
        if code in mapping:
            new_mapping[mapping[code]] = id
        if str(id) in mapping:
            new_mapping[mapping[str(id)]] = (code, id)
    #     ele[code] = id
    # for key in mapping:
    #     if ele.get(key) not in new_mapping.values():
    #         print(key, mapping.get(key), ele.get(key))
    with open(args.conf_path, "w") as f:
        for string, pair in new_mapping.items():
            if isinstance(pair, tuple):
                code, id = pair
                f.write("%s,%s,%s\n" % (string, code, id))
            else:
                f.write("%s,%s\n"%(string, pair))


if __name__ == "__main__":
    main()