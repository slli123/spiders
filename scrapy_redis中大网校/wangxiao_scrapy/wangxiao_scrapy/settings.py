# Scrapy settings for wangxiao_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import sys
from pathlib import Path
from config import (
    # Redis配置
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PARAMS,
    RESULTS_DIR
)


BOT_NAME = "wangxiao_scrapy"

SPIDER_MODULES = ["wangxiao_scrapy.spiders"]
NEWSPIDER_MODULE = "wangxiao_scrapy.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "wangxiao_scrapy (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = RESULTS_DIR /'logs/scrapy.log'  # 可选：记录到文件

# redis配置
REDIS_HOST = REDIS_HOST
REDIS_PORT = REDIS_PORT
REDIS_DB = REDIS_DB
REDIS_PARAMS = REDIS_PARAMS
SCHEDULER = 'scrapy_redis.scheduler.Scheduler'
SCHEDULER_PERSIST = True
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'


SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

# 并发和性能配置
CONCURRENT_REQUESTS = 16  # 全局并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # 每个域名并发数
CONCURRENT_REQUESTS_PER_IP = 0  # 每个IP并发数，0表示不限制
DOWNLOAD_DELAY = 1  # 下载延迟（秒）
RANDOMIZE_DOWNLOAD_DELAY = True  # 随机延迟
DOWNLOAD_TIMEOUT = 30  # 下载超时时间

# 重试配置
RETRY_ENABLED = True
RETRY_TIMES = 5  # 最大重试次数
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403]

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False
# 启用深度优先
DEPTH_PRIORITY = 1  # 深度优先级
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "wangxiao_scrapy.middlewares.WangxiaoScrapySpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   "wangxiao_scrapy.middlewares.WangxiaoScrapyDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html

ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline': 301,
    "wangxiao_scrapy.pipelines.WangxiaoScrapyPipeline": 300,
}

# 优先级配置
SCHEDULER_PRIORITY_QUEUE = 'scrapy_redis.queue.PriorityQueue'

# 自动限速扩展
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# 内存限制（防止内存泄漏）
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048  # 最大内存限制2GB
MEMUSAGE_WARNING_MB = 1024  # 内存警告阈值1GB
MEMUSAGE_NOTIFY_MAIL = []  # 邮件通知（可选）
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
