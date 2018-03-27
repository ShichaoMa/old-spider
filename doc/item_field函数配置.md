item_xpath中每个spider对应着一个列表排列着要抓取的所有字段及其配置信息，你问我字段列表为什么不用字典而用列表套元组，因为字典不能排序，然而每个字段的抓取顺序，都框架来说很重要，一些深入的特性将在本节讲到，请仔细阅读哦！ (*^__^*)
举个栗子先，下面是bluefly的字段列表，已被我拿来多次使用了，声明，我不是在做蓝翔的软广。。bluefly不是蓝翔！(*>﹏<*)
```
[ # 要抓取的字段
            ('retail_price', { # 价格字段
                "xpath": [ # 提取方式, 还可以使用re, css表达式，按xpath, re, css顺序逐一提取，三者至少选择一个
                    '//*[@id="product-selection"]//span[@class="mz-price-retail-label"]/../text()', # 表达式
                    .... # 可以配置多个，如果第一个表达式提取为空，会使用下一个表达式提取
                ],
                "function": format_html_xpath_common, # 将提取结果转换成所需要的格式，可无，使用默认转换函数
                "extract": lambda item, response: image_urls_from(safely_json_loads(item["color_images"])), # 抽取函数，若转换函数调用完毕之后返回空，则会调用该函数，并返回结果，否则无效。 可无
                "default": "$100" # 默认值， 可无
                "request": lambda item, response: (
(urljoin(item['response_url'],''.join(response.xpath('//div[@id="unqualifiedBuyBox"]/div/div[1]/a/@href').extract()).strip()) if item['availability'] == 'other' else None), None, None, None), # 若通过function, extract之后得到的值仍然为空，则提供url做增发请求操作，用于在其它页面中获取所需值。该函数应该返回一个包含url, cookie, method, body的元组，没有的话设置为None。其它页面抽取所需值的选择器及选择表达式可配置到xpath, re, css对应的表达式中，下一个页面使用的转换函数和抽取函数可以使用之前的函数，也可以单独配置，配置的名称为function_after以及extract_after，函数结构保持一致。可无
                "skip": True # 若为True，则这个字段仅存在于抓取函数处理过程中，pipline中会略过这个字段，可无
           }),
       ]
```
其中，function对应转换函数， extract对应抽取函数，request对应其它页面链接返回函数，这里需要一点scrapy知识，scrapy通过Selector进行页面解析，Selector实例有三个方法，xpath, re, css， xpath用的最广，css几乎不用，虽然本框架支持css，但是不推荐使用，不听话，出了bug不概不负责哦！(＝^ω^＝)。xpath函数通过一个xpath,返回xpath配置到的所有信息的Selector对象，调用该对象的extract方法可以返回所有信息的列表，如果没有抓取到任何信息，则返回空列表。re函数返回re表达式中匹配到的所有组的列表。
对于function及extract函数，字段名称为key，返回值直接做为value存储到结果集item中，下一个字段的函数可以直接使用item中的值，这就是为什么要保证字段抓取顺序的原因。下面分别对函数的规范进行讲解。
- function: # 转换函数 若为没有此字段，则使用默认转换函数（见下一节）
  - param1:选择器选择结果Selector实例
  - param2:结果集item（其中包含按顺序抽取完毕的字段值）
  - return:有效字段或空
- function_after: # 增发请求时特定转换函数
  - 同上
- extract: # 抽取函数
  - param1:结果集合item（其中包含按顺序抽取完毕的字段值）
  - param2:响应对象 HtmlResponse对象
  - return:有效字段或空
- extract_after: # 增发请求特定抽取函数
  - 同上
- request: # 增发请求函数
  - param1:item 结果集合item（其中包含按顺序抽取完毕的字段值）
  - param2:响应对象 HtmlResponse对象
  - return:（url, cookie, method, body）除url 其它可设为None
各函数执行顺序 function, extract, request, function_after, extract_after,任意函数只要返回了非空值，则执行中止，非空值作为该字段对应值存储到item结果集

### 注：需要增发请求的字段应放在所有字段的最后面，如果有字段放在了增发请求的字段后面，那么该字段将从增发的响应页面中获取，后续字段还可以继续增发请求，理论上可以无限增发。举个例子，第一个项目页面获取到了基本信息product_id, title，price，获取size字段时增发了一个请求，color字段在size字段的后面，那么color字段如果不继续增发请求的话，将使用size增发响应的页面获取。如果color页面也做了增发请求，将在下一次响应时获取color字段。如果size字段后面跟随了一个price字段，则通过增发请求得到的price（若不为空）将覆盖掉之前得到的price。

## 公共函数
公共函数位于walker.spiders.helper模块中导入即可使用

### 公共转换函数
以下4个公共转换函数适用于大多数简单情况，直接在function中配置即可
- function_xpath_common # 默认xpath转换函数
- function_re_common # 默认re转换函数
- format_html_xpath_common # 若从网页中抽取一段html，可以使用该函数格式化
- safely_json_re_common # 若从网页中抽取一段json数据，可以使用该函数格式化

### 工具函数
- xpath_exchange # 将一个Selector对象的结果抽取出来并合并成一个字符串
- re_exchange # 将re表达式返回的列表结果合并成一个字符串
