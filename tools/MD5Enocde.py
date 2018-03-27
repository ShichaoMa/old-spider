# -*- coding:utf-8 -*-
import os
import traceback

from hashlib import md5


def md5_encode(filename):
    md = md5()
    md.update(open(filename, "rb").read())
    return md.hexdigest()


def main():
    path = "/mnt/nas/pi/images_store/amazon"
    for root, dirs, files in os.walk(path):
        for f in files:
            filename = os.path.join(root, f)
            if f.endswith("jpg") and f.count("_") == 0 and not os.path.exists(filename[:-3]+"md5"):
                try:
                    print("Find image named %s. "%filename)
                    open(os.path.splitext(filename)[0] + ".md5", "w").write(md5_encode(filename))
                except Exception:
                    traceback.print_exc()


if __name__ == "__main__":
    main()

# ashford
# eastbay
# zappos