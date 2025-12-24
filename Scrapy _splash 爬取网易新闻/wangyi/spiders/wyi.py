import scrapy
from scrapy_splash.request import SplashRequest
from scrapy import Selector  # 直接在顶部导入，不用在parse里临时导入
from wangyi.items import WangyiItem

lua_source = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))
--准备一个js函数预加载
-- jsfunc是lua预留与JavaScript结合使用的
get_btn_display = splash:jsfunc([[
    function(){

    return document.getElementsByClassName('load_more_btn')[0].style.display;

  }
    ]])

while(true)
do
	splash:runjs("document.getElementsByClassName('load_more_btn')[0].scrollIntoView(true)")
	splash:select(".load_more_btn").click()
  splash:wait(1)
  --判断load_more_btn是否为None
  display = get_btn_display()
  if(display=='none')
    then
      break
    end
end 

  return {
    html = splash:html()
  }
end
"""

class WyiSpider(scrapy.Spider):
    name = "wyi"
    allowed_domains = ["163.com"]
    start_urls = ["https://news.163.com/"]

    async def start(self):
        yield SplashRequest(
            url=self.start_urls[0],
            callback=self.parse,
            endpoint="execute",  # 终端表示要执行使用splash哪一个服务
            args={
                "lua_source":lua_source,  # 执行lua脚本
                'url':self.start_urls[0]
            }
        )

    def parse(self, response):
        # 1. 解析Splash返回的JSON
        # print(response.text)
        result = response.data   # response.data：解析后的 JSON 字典（对应你的 lua 脚本返回的内容）
        html_content = result['html']

        # 2. 把HTML字符串转换成Selector对象（才能用xpath）
        selector = Selector(text=html_content)

        # print(selector)
        #3. 开始解析数据
        for content in selector.xpath('//*[@id="index2016_wrap"]//div[@class="data_row news_article clearfix "]'):
            item = WangyiItem()
            title = content.xpath('.//div[@class="news_title"]/h3/a/text()').extract_first()
            title_url = content.xpath('.//div[@class="news_title"]/h3/a/@href').extract_first()
            time = content.xpath('.//span[@class="time"]/text()').extract_first()
            item['title'] = title
            item['title_url'] = title_url
            item['time'] = time
            yield item