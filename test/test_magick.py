# -*- coding:utf-8 -*

from pgmagick import gminfo

print gminfo().version

from pgmagick import Image, FilterTypes, Geometry, Color

a = ("/mnt/nas/pi/images_store/gnc/08f/250/7024c5c558d1bedf710977342875f1138f/08f2507024c5c558d1bedf710977342875f1138f.jpg")


im = Image(a)
print dir(im)
im.crop(Geometry("400x400"))
im.write("a.jpg")