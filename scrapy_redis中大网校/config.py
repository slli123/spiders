#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网校Cookie获取配置文件 - 第一步：只配置当前需要的
"""

import os
from pathlib import Path

# ==================== 基础路径 ====================
# 项目根目录（自动计算）
BASE_DIR = Path(__file__).parent.absolute()

# ==================== 网站登录配置 ====================
# 网校账号（必填）
USERNAME = ""  # 你的网校登录账号
PASSWORD = ""  # 你的网校登录密码
LOGIN_URL = "https://ks.wangxiao.cn/"  # 登录页面

# ==================== 超级鹰配置 ====================
# 超级鹰打码平台（必填）
CHAOJIYING_USERNAME = ""  # 你的超级鹰用户名
CHAOJIYING_PASSWORD = ""  # 你的超级鹰密码
CHAOJIYING_SOFT_ID = ""  # 软件ID（你的）
CHAOJIYING_CODE_TYPE = "8001"  # 验证码类型

# ==================== Selenium浏览器配置 ====================
# 浏览器驱动路径（重要！）
DRIVER_PATH = str(BASE_DIR / "webdriver" / "msedgedriver.exe")  # Edge驱动
# 如果要用Chrome，但相应的cookie_get.py文件导入的包也要修改：
# DRIVER_PATH = str(BASE_DIR / "webdriver" / "chromedriver.exe")

# ==================== redis数据库配置 ====================
REDIS_HOST = "localhost"  # 你的数据库地址
REDIS_PORT = 6379    # 你的端口
REDIS_DB = 5    # 选择的库
REDIS_PARAMS = {
    'password': '',  # 密码

}

# ==================== MySQL数据库配置 ====================
# MySQL连接配置
MYSQL_CONFIG = {
    'host': 'localhost',  # 数据库地址
    'user': 'root',   # 需要root用户登录，这里不用修改
    'password': '',   # 你的密码
    'database': '',   # 你的数据库
    'charset': 'utf8mb4'
}

# 浏览器窗口设置
WINDOW_WIDTH = 1920  # 窗口宽度
WINDOW_HEIGHT = 1080  # 窗口高度
# 无头模式专用优化配置
HEADLESS_OPTIMIZATIONS = {
    "disable_gpu": True,          # 禁用GPU加速（无头模式下必须）
    "no_sandbox": True,           # 无沙盒模式
    "disable_dev_shm": True,      # 禁用共享内存
    "single_process": False,      # 单进程模式（避免内存泄漏）
}


# ==================== 运行参数配置 ====================
# Cookie获取频率
RUN_INTERVAL_HOURS = 12  # 每12小时获取一次Cookie
MAX_RETRIES = 3  # 失败重试次数
RETRY_DELAY = 300  # 重试等待时间（秒）


# 超时设置
PAGE_LOAD_TIMEOUT = 60  # 页面加载超时（秒）
ELEMENT_WAIT_TIMEOUT = 20  # 元素等待超时（秒）
IMPLICIT_WAIT = 15  # 隐式等待时间（秒）

# ==================== 文件路径配置 ====================
# 结果目录（自动创建）
RESULTS_DIR = BASE_DIR / "results"
COOKIES_DIR = RESULTS_DIR / "cookies"  # Cookie保存目录
CAPTCHA_DIR = RESULTS_DIR / "captchas"  # 验证码图片目录
SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"  # 错误截图目录
LOGS_DIR = RESULTS_DIR / "logs"  # 日志目录

# 创建所有需要的目录
for directory in [RESULTS_DIR, COOKIES_DIR, CAPTCHA_DIR, SCREENSHOTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 具体文件路径
COOKIE_LATEST_FILE = str(COOKIES_DIR / "cookies_latest.json")  # 最新Cookie文件
CAPTCHA_TEMP_FILE = str(CAPTCHA_DIR / "captcha_temp.jpg")  # 验证码临时文件
ERROR_SCREENSHOT_FILE = str(SCREENSHOTS_DIR / "error_{timestamp}.png")  # 错误截图
LOG_FILE = str(LOGS_DIR / "cookie_fetcher.log")  # 日志文件




# ==================== 登录页面元素定位 ====================
# 如果网站改版，只需要修改这里的XPath
LOGIN_ELEMENTS = {
    # 登录入口按钮
    "login_button": '//*[@id="_login1"]',

    # 切换到密码登录的标签
    "password_tab": '//*[@id="tab-click"]//*[contains(text(), "密码登录")]',

    # 验证码图片
    "captcha_image": '//*[@id="nimg-code"]/img',

    # 输入框
    "username_input": '//*[@id="username"]',
    "password_input": '//*[@id="pwd"]',
    "captcha_input": '//*[@id="ncode"]',

    # 登录提交按钮
    "submit_button": '//*[@id="login-normal"]',
}
