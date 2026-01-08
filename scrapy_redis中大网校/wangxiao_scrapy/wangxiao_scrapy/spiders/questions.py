import scrapy
from scrapy_redis.spiders import RedisSpider,RedisCrawlSpider
from scrapy.linkextractors import LinkExtractor
import json
from pathlib import Path
from ..items import WangxiaoScrapyItem

class QuestionsSpider(RedisSpider):
    name = "questions"
    allowed_domains = ["ks.wangxiao.cn"]
    # start_urls = ["https://ks.wangxiao.cn/"]
    redis_key = "questions:url"

    def __init__(self,*args,**kwargs):
        super(QuestionsSpider,self).__init__(*args,**kwargs)
        self.cookies = self.load_cookies_from_file()


    def load_cookies_from_file(self):
        """从文件加载Cookie"""
        PROJECT_ROOT = Path(__file__).resolve().parents[3]
        cookie_file = PROJECT_ROOT / "results" / "cookies_latest.json"
        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cookies = data.get('cookies', {})
                    self.logger.info(f"✅ 从文件加载 {len(cookies)} 条Cookie")
                    return cookies
            except Exception as e:
                self.logger.error(f"加载Cookie文件失败: {e}")

        self.logger.warning("Cookie文件不存在或加载失败")
        return {}

    def parse(self, response,**kwargs):
        self.logger.info('开始解析-->获取题目类型url')
        meta = response.meta.copy()

        ls =LinkExtractor(restrict_xpaths='//*[@id="banner"]//ul/li/div[@class="send-title"]/a')
        send_url_list = ls.extract_links(response)
        for send_url in send_url_list:
            # print(send_url.url)
            # print(send_url.text)
            first_url= send_url.url
            first_url = first_url.replace('TestPaper','exampoint')
            frist_title = send_url.text
            meta['first_title'] = frist_title
            yield scrapy.Request(
                url=first_url,
                callback=self.parse_second_page,
                meta=meta,
                priority=-10
            )

    def parse_second_page(self,response,**kwargs):
        self.logger.info('第二层url解析开始----')
        meta = response.meta.copy()

        # print(first_title)
        ls = LinkExtractor(restrict_xpaths='/html/body//div[@class="filter-item"]/a')
        send_url_list = ls.extract_links(response)  # 把科目的给提取出来
        for send_url in send_url_list:
            second_url= send_url.url
            second_title = send_url.text
            # print(second_url,second_title)
            meta['second_title'] = second_title
            yield scrapy.Request(url=second_url,
                                 callback=self.parse_third_page,
                                 meta=meta,
                                 priority=-1
                                 )

    def parse_third_page(self,response,**kwargs):
        self.logger.info(f'开始获取题目相关信息')
        meta = response.meta.copy()
        post_url = "https://ks.wangxiao.cn/practice/listQuestions"

        son_points = response.xpath('/html/body/div//ul[@class="section-point-item"]')
        if son_points:
            for son_point in son_points:
                father_points = son_point.xpath('ancestor::ul[@class="section-item" or @class="chapter-item"]')
                father_names = [meta['first_title'],meta['second_title']]
                for father_point in father_points:
                    father_name = father_point.xpath('./li[@class="fl"][1]/text()').extract()

                    father_name = ''.join(father_name).replace(' ','').replace('\n','').replace('\t','').replace('\r','')
                    father_names.append(father_name)

                son_name = son_point.xpath('./li[@class="fl"][1]/text()').extract()
                son_name = ''.join(son_name).replace(' ','').replace('\n','').replace('\t','').replace('\r','')
                father_names.append(son_name)
                meta['father_names'] = father_names
                # print('第一',father_names)
                # 接下来就是找参数了
                # 把那几个参数找到然后丢接口，然后发送请求
                data_number = son_point.xpath('./li[@class="fl"][2]/text()').extract_first().split('/')[1]
                data_sign = son_point.xpath('./li[@class="fl"]/span/@data_sign').extract_first()
                data_subsign = son_point.xpath('./li[@class="fl"]/span/@data_subsign').extract_first()
                # print('第一',data_number,data_sign,data_subsign)
                # 传参
                data_post = {
                    'examPointType':'',
                    'practiceType':'2',
                    'questionType':'',
                    'sign':data_sign,
                    'subsign':data_subsign,
                    'top':data_number,
                }
                yield scrapy.Request(url=post_url,
                                     method="POST",
                                     body=json.dumps(data_post),
                                     cookies=self.cookies,
                                     headers={
                                         'x-requested-with': 'XMLHttpRequest',
                                         'accept':'application/json, text/javascript, */*; q=0.01',
                                         'Content-Type':'application/json; charset=UTF-8'
                                     },
                                     callback=self.parse_get_json,
                                     meta=meta,
                                     priority=200
                                     )


        else:
            points = response.xpath('/html/body//div/ul[@class="chapter-item"]')
            for point in points:
                father_names = [meta['second_title'],meta['second_title']]
                son_name = point.xpath('./li[@class="fl"][1]/text()').extract()
                son_name = ''.join(son_name).replace(' ','').replace('\n','').replace('\t','').replace('\r','')
                father_names.append(son_name)
                meta['father_names'] = father_names
                # print('第二',father_names)

                data_number = point.xpath('./li[@class="fl"][2]/text()').extract_first().split('/')[1]
                data_sign = point.xpath('./li[@class="fl"]/span/@data_sign').extract_first()
                data_subsign = point.xpath('./li[@class="fl"]/span/@data_subsign').extract_first()
                # print('第二',data_number,data_sign,data_subsign)

                data_post = {
                    'examPointType':'',
                    'practiceType':'2',
                    'questionType':'',
                    'sign':data_sign,
                    'subsign':data_subsign,
                    'top':data_number,
                }
                yield scrapy.Request(url=post_url,
                                     method="POST",
                                     body=json.dumps(data_post),
                                     cookies=self.cookies,
                                     headers={
                                         'x-requested-with': 'XMLHttpRequest',
                                         'accept':'application/json, text/javascript, */*; q=0.01',
                                         'Content-Type':'application/json; charset=UTF-8'
                                     },
                                     callback=self.parse_get_json,
                                     meta=meta,
                                     priority=200
                                     )

    def parse_get_json(self,response):
        meta = response.meta.copy()
        title_all = meta.get('father_names')
        # print(response.url)
        tile = ''.join(title_all)
        all_data = response.json().get('Data')
        if all_data:
            self.logger.info(f'开始解析题目《{tile}》')
            all_q = [] # 把这一整道题的都掏出来 就一个post接口的 都是一个类型的
            # 题目可能有选择题，判断题，多项选择，不定项选择，材料题......
            for data in all_data:
                # if data.get("paperRule"):  # 题目类型
                #     data_type = data.get("paperRule")
                #     data_type = data_type.get("content")
                #     data_type = {"data_type": data_type}
                    # all_q.append(data_type)    # 不符合redis的逻辑了，原本用来生成题目类别下的，舍弃不管了
                    # TM会在下面给生成单独的item了，原本是可以符合scrapy直接按循序在pipslines中直接写入文件即可，
                    # 舍弃

                if data.get("questions"):
                    q = data.get("questions")
                    all_q.extend(q)
                if data.get("materials"):
                    m = data.get("materials")
                    all_q.extend(m)


            for q in all_q:
                # 完整的一道题：类型 -> 题目 -> 选项 -> 正确答案 -> 解析
                item = WangxiaoScrapyItem()
                item['path'] = title_all
                # if q.get("data_type"):  # 类型
                #     data_type = q.get("data_type")
                #     item['data_type'] = data_type

                if q.get("content"):
                    content = q.get("content")  # 题目
                    item['content'] = content

                option = []
                option_isRight = []
                if q.get('options'):  # 选择题处理
                    options = q.get('options')
                    for i in options:
                        content = i.get("content", "")  # 选项内容，
                        name = i.get("name", "")  # 选项字母，
                        isRight = i.get("isRight")  # 是否正确答案 是否为1
                        if name and content:
                            contents = f'{name}、{content}'
                            option.append(contents)
                        if isRight in [1, True]:
                            option_isRight.append(name)
                    item['options'] = option

                # 拼接正确答案
                if q.get("textAnalysis"):
                    textAnalysis = q.get("textAnalysis")
                    textAnalysis = ''.join(option_isRight) + textAnalysis
                    item['textAnalysis'] = textAnalysis

                if q.get("material"):
                    con = q.get("material")
                    content_1 = con.get("content", "")  # 材料部分内容
                    content_2max = q.get("questions", [])  # 子题部分

                    try:
                        for content_2 in content_2max:
                            if content_2.get("content") and content_1:
                                content = content_2.get("content")
                                content_a = f'{content_1}\n{content}'
                                item['content'] = content_a
                            elif content_2.get("content"):
                                item['content'] = content_2.get("content")

                            sub_option = []
                            sub_option_isRight = []
                            if content_2.get('options'):
                                options = content_2.get('options')
                                for i in options:
                                    content = i.get("content", "")
                                    name = i.get("name", "")
                                    isRight = i.get("isRight")
                                    if name and content:
                                        contents = f'{name}、{content}'
                                        sub_option.append(contents)
                                    if isRight in [1, True]:
                                        sub_option_isRight.append(name)
                                item['options'] = sub_option

                            # 子题解析拼接正确答案
                            if content_2.get("textAnalysis"):
                                textAnalysis = content_2.get("textAnalysis")
                                textAnalysis = ''.join(sub_option_isRight) + textAnalysis
                                item['textAnalysis'] = textAnalysis

                    except TypeError:
                        pass
                    continue
                # print('题目爬取完成',item)
                yield item

            self.logger.info(f'题目《{tile}》解析完成，开始存入reids数据库')
        else:
            self.logger.info(f"题目《{tile}》解析失败，相应状态码{response.status},url为{response.url}")
