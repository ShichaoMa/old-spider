# -*- coding:utf-8 -*-
import time, glob, ftplib
file_dir = "/home/ubuntu/ftp_file"
with ftplib.FTP(host="ftp.jinanlongen.com", user="cosmopolitanusa", passwd="Cosmo!Usa!123") as ftp:
    ftp.cwd("items")
    while True:
        try:
            local_files = set(glob.glob("%s/*.txt" % file_dir))
            for i in ftp.nlst():
                if i not in local_files and i.endswith("txt"):
                    with open("%s/%s"%(file_dir, i), "w") as f:
                        ftp.retrlines("RETR %s"%i, f.write)
                    local_files.add(i)
        except Exception as e:
            print(e)
        time.sleep(60)