import requests

headers = {#'pragma': 'no-cache',
           'cookie': #'AKA_A2=1; RESOURCEINFO=DEVICE=desktop&ORIGINALDEVICE=desktop; '
                     'ytos-session-MONCLER=3452f1c098a448f58fcc11c0ed9381397cgIbZB2VxtfSWx6xLm8ng; '
               #      'UI-PERSISTENT=abtest=&abtestperc=&abtesth=4SObxciWWbbS2MCyf8Sq6Q&country=us; '
               #      'UI=abtest=&abtestperc=&abtesth=4SObxciWWbbS2MCyf8Sq6Q&cacheversion=f31-v363-moncler-w&device=desktop&version=2017-11-02-073faaf&lang=; '
               #      'TS013509ec=0122c051bc0442382618513c0d12ebca170b9bdc282fb867d94b66b7de529cd56f2937591b08fc9d72b68d2addcc6b8b42928bdda6e26835a45b950b4cc9b65e37fbe27bde; '
               #      'YEDGESESSION=0a77973f6a2c00001cc4fb599f030000f3040000; JSESSIONID=00008eVBE9C6zMwJy6Vr16VgnRS:-1; '
               #      'AWSELB=9D77CF831C27CD9CAB801D7DEDFF840A49150DD23605472042E466560784FF50A1691AE36E72329803913C208177B762E84971F3B62BB2AEEAEF395558D47BAA8E7BCE69C4736FE73C015250CFCA082EDEAFB636BF; '
               #      '_ceg.s=oyz256; '
               #      '_ceg.u=oyz256; '
               #      'optimizelyEndUserId=oeu1509938039925r0.3710667129584371; '
               #      'font-loaded=1; Y-Country-Language=en-us; '
               #      'ak_bmsc=D86B797576EF999ECC3810FC6714F6BBA5FE600CB87A00007307005A4741544B~plSFQE0GN1dUMtOO0/ewFB1oCGDty9g+kMuLUf2aFffHOlUVmoCJkxWh8jM99BJVOi3o5hxzdHKpQiC2UX7t0qx6670dAs4ZRLKA5HWt9LGO3/8F/jU4p+lzo5cZ4BUhe7+93abdRF6MmaqPx+F4jfJH9mpLdQKq7U7A7+TNFae7m/MzQue6yICDmTxS+X11TjgEr1/H94vBsPT0AFIiJKKZXAq33KoT5EOjDCdGMPUE8=; '
               #      'dtSa=-; '
               #      'dtLatC=6; '
               #      'optimizelySegments=%7B%223729740363%22%3A%22none%22%2C%223756210030%22%3A%22gc%22%2C%223760630132%22%3A%22false%22%2C%223762480025%22%3A%22referral%22%2C%225532531155%22%3A%22true%22%7D; '
               #      'optimizelyBuckets=%7B%7D; '
               #      'VISIT=NAZIONE=UNITED+STATES&NAZIONE_ISO=US&LANGID=19&SITE_CODE=MONCLER_US; '
               #      'TS014254ab=0122c051bc02db7295e7df7da1f673eae8f99c85742fb867d94b66b7de529cd56f2937591be28b9d4cc34cb623e4563cde27a64f1c8fac0751d791825908892baf5e5408fb83fcc22db16eb58d6e69729fea8ec493a34573bf3567fa94511d15920dae6d9e5356da34db6f4c08d8a1234985765684; '
               #      '_ga=GA1.2.1652527186.1509005794; '
               #      '_gid=GA1.2.542530808.1509930903; '
               #      '_ceg.s=oyzmp5; _ceg.u=oyzmp5; '
               #      'yOrbRD=guid%3De1f2ed21-ed8b-4ad5-b66c-312f71ed46f7; '
               #      'rxVisitor=15099380392135UR7JO64DRBU74IT6QC22GKIVF69GMM0; '
               #      'dtCookie=3$A151CD38A4A6941BAB01856A35751EEE|store.moncler.com|1; '
               #      'TS0143c829=0122c051bc5bd2057ed6ef8ddae3c0cd23404c26f0a1e3bd7fe15c6e4d8781f1b9dc5b2b55dcd5b70ea65ae98178de7b5521d85132; '
               #      'bm_sv=AE10B3249B47E88D68DA23B81863A07A~+gshhCd9mBWPFABka6ly0AjeujNMwNXCfUUiSEz3eJIHBuDw3dtsXk3rO4JunCag005InE7rvTyAHnR2TAybCn+/TpONmrwgqlLleLvI/BoG5olhN0CraIlLH9Ff+yeLZIWEnz7XnovewO4xJ7y+htpqwB/0KOspvphlNHJp/ZE=; '
               #      'rxvt=1509959627532|1509950667873; '
               #      'dtPC=3$355610519_27h51vCRJIMELKFPRDJHMEITMKGHPNBJCAHMIINL'
                    '',
           'accept-encoding': 'gzip, deflate, br',
           'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36',
           'accept': '*/*',
           #'cache-control': 'no-cache',
           #'authority': 'store.moncler.com',
           #'x-requested-with': 'XMLHttpRequest',
           #'referer': 'https://store.moncler.com/en-us/outerwear_cod872910525976.html'
            }

url = 'https://store.moncler.com/yTos/Plugins/ItemPlugin/RenderItemPrice?siteCode=MONCLER_US&code10=872910525976&options.priceType=RenderItemPrice&options.siteCode=MONCLER_US&options.code10=872910525976&options.disableAjaxUpdate=false&options.enableAjaxUpdateOnColorChanges=true&options.pricePriority=6&options.priceScope=0&options.enableAjaxupdate=true'
print(requests.get(url, headers=headers).text)