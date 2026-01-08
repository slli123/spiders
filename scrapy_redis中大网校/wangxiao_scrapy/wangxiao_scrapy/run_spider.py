#!/usr/bin/env python3
"""
启动脚本：用于初始化Redis队列和启动爬虫
"""
import redis
import time
import sys
from pathlib import Path


def init_redis_queue():
    """初始化Redis队列"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # 清空旧队列
    r.delete('questions:start_urls')
    r.delete('questions:requests')
    r.delete('questions:dupefilter')

    # 添加起始URL
    start_urls = [
        "https://ks.wangxiao.cn/",
        # 可以添加更多的起始URL
    ]

    for url in start_urls:
        r.lpush('questions:start_urls', url)

    print(f"✅ 已添加 {len(start_urls)} 个起始URL到Redis队列")
    return len(start_urls)


def monitor_queue():
    """监控队列状态"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    while True:
        try:
            queue_size = r.llen('questions:start_urls')
            requests_size = r.llen('questions:requests')
            dupefilter_size = r.scard('questions:dupefilter')

            print(f"\r📊 队列状态: 待处理URL={queue_size}, 待处理请求={requests_size}, 已过滤={dupefilter_size}", end='')
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 停止监控")
            break
        except Exception as e:
            print(f"\n❌ 监控错误: {e}")
            break


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        monitor_queue()
    else:
        count = init_redis_queue()
        print(f"初始化完成，可以使用以下命令启动爬虫：")
        print(f"scrapy crawl questions")
        print(f"或使用多进程启动：")
        print(f"python run_multiprocess.py")