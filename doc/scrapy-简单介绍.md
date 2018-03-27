scrapy 是一个流行的python爬虫框架，本二次开发框架基于scrapy开发完成，实现通用部分，仅需要少量配置性代码即可完成一个网站的特定抓取工作
### scrapy 运行简单分为四个步骤
- 任务分配

任务分配是由scheduler完成的， 主要的工作函数为enqueue_request和next_request，enqueue_request可以将下载和解析过程中返回的抓取任务请求在放回到队列中。本框架中，返回的抓取任务主要分为三种，第一种是下载出错或者解析出错，被要求重试或重定向时将原任务返回给队列；第二种是解析过程中发现符合要求的链接，比如刚开抓取分类链接，分类链接下面包含很多项目链接，那每个项目链接都是一个符合要求的链接；第三种是抓取项目链接中，有需要增发请求来达到抓取效果的链接，也会被返回。next_request会从任务队列返回一个任务请求，用以下载。任务队列采用redis实现，以优先级排序，优先级大者优先进行抓取。
- 下载

scrapy下载使用的twisted异步架构，可以在settings配置并发数量及超时时间，下载前，请求会依次通过下载中间件的process_request。用来对请求进行处理，比如增加user-agent等其它请求头，增加代理配置等等，下载结束后，如果下载没有出错，那么响应会依次倒序通过process_response,对响应进行处理，最后会调用callback函数，在本框架中，分类请求的callback函数为parse函数，子项目请求的callback函数为parse_item函数。如果下载出错，则会依次倒序通过process_exception，最后调用request errorback函数（settings中需要配置HTTPERROR_ALLOW_ALL=True）。
- 解析

通过回调函数parse和parse_item，我们可以从响应体中获取重要信息。比如本框架通过parse函数获取下一页链接及子项目链接，然后生成新的请求，返回给任务队列；通过parse_item函数抓取我们配置好的字段，比一件商品的标题，品牌，价格，尺寸，图片等等，将这些信息保存到一个自定义的Item类实例（结果集）中，然后返回该实例。
- 持久化结果集

scrapy通过pipline来处理结果集。item实例依次通过每个pipline的process_item函数，可以通过dict(item)将数据集转换为字典类型，然后将其保存到文件，excel, mysql, mongodb, hbase等数据库中。

具体开发流程请参照官方文档[Scrapy 1.2 documentation](https://doc.scrapy.org/en/latest/index.html)