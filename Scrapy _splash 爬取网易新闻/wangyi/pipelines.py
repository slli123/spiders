import csv
import os


class WangyiPipeline:
    def __init__(self):
        self.csv_file_path = "../wangyi_news.csv"
        self.csv_headers = ["title", "title_url", "time"]
        self.file = open(self.csv_file_path, "w", encoding="utf-8", newline="")
        self.csv_writer = csv.DictWriter(self.file, fieldnames=self.csv_headers)

        if os.path.getsize(self.csv_file_path) == 0:
            self.csv_writer.writeheader()

    def process_item(self, item, spider):
        print("爬取成功的数据", item)
        # 将Scrapy Item对象转为普通字典，写入CSV
        self.csv_writer.writerow({
            "title": item.get("title", ""),  # get方法避免字段为空报错
            "title_url": item.get("title_url", ""),
            "time": item.get("time", "")
        })

        self.file.flush()
        return item

    def close_spider(self, spider):
        self.file.close()
        print(f"爬虫结束，数据已保存至：{self.csv_file_path}")