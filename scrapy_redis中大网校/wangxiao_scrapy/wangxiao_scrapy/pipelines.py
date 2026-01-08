# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import logging

class WangxiaoScrapyPipeline:
    def process_item(self, item, spider):
        # 必须返回item，否则RedisPipeline收不到
        return item