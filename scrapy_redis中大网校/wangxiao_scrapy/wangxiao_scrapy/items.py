# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WangxiaoScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    data_type = scrapy.Field()
    content = scrapy.Field()
    options = scrapy.Field()
    textAnalysis = scrapy.Field()
    path = scrapy.Field()

