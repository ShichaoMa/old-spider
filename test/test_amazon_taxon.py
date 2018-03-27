from requests import get
import webbrowser
import os


url = "https://www.amazon.com/s/ref=sr_in_g_p_89_7?fst=as%3Aoff&rh=n%3A7141123011%2Cn%3A7147440011%2Cn%3A7192394011%2Cn%3A7454939011%2Cp_89%3AGem+Stone+King&bbn=7454939011&ie=UTF8&qid=1509420935&rnid=2528832011"

headers = {
                #'Pragma': 'no-cache',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en',
               #'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               #'Referer': 'https://www.amazon.com/Converse-Unisex-Chuck-Taylor-Sneakers/dp/B0059NGJSU/ref=lp_679260011_1_1?s=apparel&ie=UTF8&qid=1505447322&sr=1-1&nodeID=679260011&psd=1&th=1&psc=1',
               #'Connection': 'keep-alive',
               #'Cache-Control': 'no-cache'
               }

def main(page):

    resp = get(url + "&page=%s"%page, headers=headers, proxies={"https": "http://longen:jinanlongen2016@mx13.headedeagle.com:12017"})

    with open("test.html", "w") as f:
        f.write(resp.text)
    webbrowser.open("file://%s"%os.path.abspath("test.html"))


main(400)
