- 单商品货号更新
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 0
      - urlsfile: 文件，每行一个单品货号，例如：DFS545GFDS4
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - crawlid: default=%Y%m%d%H%M%S
      - priority: default=1
    - enctype: multipart/form-data
  - return: 指定商品/单品(amazon)的部分信息，不会处理图片。
- 单商品链接更新
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 1
      - urlsfile: 文件，每行一个单品链接，例如：http://www.amazon.com/dp/AD9FSNFD0/ref=?utf-8
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - crawlid: default=%Y%m%d%H%M%S
      - priority: default=1
    - enctype: multipart/form-data
  - return: 指定商品的部分信息，不会处理图片。
- 单分类抓取
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 2
      - urls: http://www.example.com/{4个空格}http://www.amazon.com/
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - crawlid: default=%Y%m%d%H%M%S
      - priority: default=1
  - enctype: multipart/form-data
  - return: 分类下的全部商品信息
- 多分类抓取
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 3
      - urlsfile: 文件，每行一个crawlid和分类链接，4个空格分隔：例如：11222    http://www.amazon.com/
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - priority: default=1
  - enctype: multipart/form-data
  - return: 多个分类下的全部商品信息
- 单商品抓取
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 4
      - urlsfile: 文件，每行一个单品链接，例如：http://www.amazon.com/dp/AD9FSNFD0/ref=?utf-8
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - crawlid: default=%Y%m%d%H%M%S
      - priority: default=1
    - enctype: multipart/form-data
  - return: 指定商品的全部信息
- 单商品更新(无需文件)
  - end point: /feed/crawl
  - method: POST
  - data:
    - require:
      - type: 5
      - urls: 要更新的商品链接 例如：http://www.example.com/{4个空格}http://www.amazon.com/
      - spiderid: 要更新的网站spider名称 例如：amazon
    - option:
      - crawlid: default=%Y%m%d%H%M%S
      - priority: default=1
    - enctype: multipart/form-data
  - return: 指定商品的部分信息，不会处理图片。
- roc分类抓取
  - end point: /api/feed
  - method: POST
  - data:
    {"type": "explore", "priority": 1, "source_site_code": "AMZN", "full": false, "url": "http://www.amazon.com", "meta": {"tags": {...}}}
  - enctype: appliction/json
  - return: 分类下的全部商品信息
- blender更新
  - end point: /api/update
  - method: POST
  - data:
    {"site": "AMZN", "messages": [{"data": {"url": "http://www.amazon.com"/,...}},]}
  - enctype: appliction/json
  - return: 指定商品链接的全部商品信息，不会处理图片，在jay有任务正在执行时，返回403。
- ws://
  - end point: /
  - data: crawlid
  - return: {{"error": true/false, "status": "finished"/"crawled"}}