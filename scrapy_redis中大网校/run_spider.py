import os
import sys
import subprocess
import redis
import signal
import logging
from pathlib import Path

# ===================== 核心配置（适配根目录结构）=====================
# 1. Redis配置（从根目录的config.py导入）
sys.path.insert(0, str(Path(__file__).absolute().parent))  # 把根目录加入Python环境
from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PARAMS,
)

REDIS_CONF = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB,
    "password": REDIS_PARAMS['password'],
    "decode_responses": True
}

# 2. Scrapy配置（定位到wangxiao_scrapy目录里的scrapy.cfg）
SCRAPY_SPIDER_NAME = "questions"
SCRAPY_PROJECT_DIR = Path(__file__).absolute().parent / "wangxiao_scrapy"  # 指向wangxiao_scrapy目录
REDIS_URL_QUEUE_KEY = "questions:url"
DEFAULT_START_URL = "https://ks.wangxiao.cn/"

# 3. 日志配置（日志放到results/logs，和根目录的results同级）
LOG_FILE = Path(__file__).absolute().parent / "results/logs/spider_runner.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)  # 自动创建日志目录

# ===================== 日志初始化 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ===================== 核心功能函数 =====================
def check_redis_connection():
    """检查Redis连接"""
    try:
        r = redis.Redis(**REDIS_CONF)
        r.ping()
        logger.info("✅ Redis连接成功")
        return r
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {e}")
        sys.exit(1)


def check_and_init_redis_queue(redis_client):
    """检查并初始化Redis URL队列"""
    try:
        queue_len = redis_client.llen(REDIS_URL_QUEUE_KEY)
        logger.info(f"📊 Redis URL队列长度: {queue_len}")
        if queue_len == 0:
            logger.warning(f"⚠️ 队列空，自动添加初始URL: {DEFAULT_START_URL}")
            redis_client.lpush(REDIS_URL_QUEUE_KEY, DEFAULT_START_URL)
            logger.info("✅ 初始URL已写入Redis")
        return queue_len
    except Exception as e:
        logger.error(f"❌ 操作Redis队列失败: {e}")
        sys.exit(1)


def run_scrapy_spider():
    """启动Scrapy爬虫（适配根目录结构）"""
    # 切换到Scrapy项目目录（wangxiao_scrapy，内含scrapy.cfg）
    os.chdir(SCRAPY_PROJECT_DIR)

    # 构建启动命令
    cmd = [
        sys.executable,  # 当前Python解释器
        "-m", "scrapy", "crawl", SCRAPY_SPIDER_NAME,
        "--logfile", str(Path(__file__).absolute().parent / "results/logs/scrapy_spider.log")
    ]

    logger.info(f"🚀 启动命令: {' '.join(cmd)}")
    logger.info(f"📌 Scrapy项目目录: {SCRAPY_PROJECT_DIR}")
    logger.info(f"📌 脚本所在根目录: {Path(__file__).absolute().parent}")

    spider_process = None
    try:
        # 启动爬虫（实时输出日志）
        spider_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1  # 行缓冲，实时输出
        )

        # 实时打印爬虫日志
        for line in iter(spider_process.stdout.readline, ''):
            if line:
                logger.info(f"[SPIDER] {line.strip()}")

        exit_code = spider_process.wait()
        if exit_code == 0:
            logger.info("✅ 爬虫正常结束")
        else:
            logger.error(f"❌ 爬虫异常退出，退出码: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        logger.warning("⚠️ 用户手动中断，停止爬虫...")
        if spider_process:
            spider_process.send_signal(signal.SIGTERM)
            spider_process.wait()
        logger.info("🛑 爬虫已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 启动爬虫失败: {e}")
        if spider_process:
            spider_process.kill()
        sys.exit(1)


def main():
    logger.info("=" * 50)
    logger.info("🎯 启动Scrapy-Redis爬虫（根目录版，和results同级）")
    logger.info("=" * 50)

    # 1. 检查Redis连接
    redis_client = check_redis_connection()
    # 2. 初始化Redis队列
    check_and_init_redis_queue(redis_client)
    # 3. 启动爬虫
    exit_code = run_scrapy_spider()

    logger.info("=" * 50)
    logger.info(f"🏁 脚本执行完成，退出码: {exit_code}")
    logger.info("=" * 50)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()