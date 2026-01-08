# 中大网校在线考试中心爬虫项目

<div align="center">

**一个模块化、解耦设计的高效爬虫系统**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

本项目采用**独立解耦的模块化设计**，各功能模块互不干扰，可根据需求灵活使用。系统包含数据抓取、存储和处理功能，适用于大规模数据采集任务。

## 🏗️ 项目架构特点

### 模块独立解耦设计
本项目采用模块化设计思想，各个模块相互独立，具有以下优势：

- **独立性**：各模块可以单独运行，互不影响
- **灵活性**：可根据需求选择性使用特定模块
- **可维护性**：单个模块的修改不会影响其他模块
- **可扩展性**：易于添加新的功能模块

**各模块职责划分：**
- `cookie_get.py`：专门负责Cookie获取，不涉及数据处理
- `run_spider.py`：专注于数据爬取，与配置和存储解耦
- `data_tools/`：独立的数据处理工具集合
- `config.py`：统一的配置管理，与其他业务逻辑分离

### 📐 项目架构图

```
                    ┌─────────────────┐
                    │   config.py     │
                    │  (统一配置)     │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────────┐
│  cookie_get.py │   │   run_spider.py │   │    data_tools/     │
│  (Cookie获取)  │   │   (数据爬取)    │   │   (数据处理)       │
└────────────────┘   └─────────────────┘   └────────────────────┘
        │                      │                       │
        │                      │                       │
        └──────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Redis数据库     │
                    │   (临时数据存储)    │
                    └─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  MySQL数据库(可选)  │
                    │   (持久化存储)      │
                    └─────────────────────┘
```

**架构说明：**
1. **配置层**：`config.py` 统一管理所有配置参数
2. **业务层**：`cookie_get.py` 和 `run_spider.py` 分别处理不同业务逻辑
3. **数据层**：Redis作为临时数据存储，支持导出到MySQL
4. **工具层**：`data_tools/` 提供数据处理和导出功能

---


## 🚀 环境要求

在开始使用本项目前，请确保已安装以下环境：

- <kbd>Python 3.10+</kbd> 或更高版本
- <kbd>Redis</kbd> 数据库
- <kbd>MySQL</kbd> 数据库（如果需要使用MySQL存储功能）

## 📁 项目结构

```
├── 📘 chaojiying.py                    # 超级鹰验证码识别服务接口
├── ⚙️ config.py                       # 项目配置文件（重要！所有配置都在这里）
├── 🔐 cookie_get.py                   # Cookie获取脚本（第一步运行）
├── 🕷️ run_spider.py                   # 爬虫主程序（第二步运行）
├── 📋 requirements.txt                # 项目依赖包列表
├── 🛠️ data_tools/                     # 数据处理工具目录
│   ├── redis_to_md.py              # 从Redis导出数据到Markdown文件
│   └── redis_to_mysql.py           # 从Redis导出数据到MySQL数据库
├── 📊 results/                        # 结果存储目录
│   ├── captchas/                   # 验证码图片存储目录
│   ├── cookies/                    # Cookie文件存储目录
│   ├── logs/                       # 日志文件存储目录
│   ├── q_all/                      # 问题数据存储目录
│   ├── screenshots/                # 错误截图存储目录
│   └── test_q/                     # 测试问题存储目录
├── 🕸️ wangxiao_scrapy/                # Scrapy爬虫框架目录
│   ├── scrapy.cfg                  # Scrapy配置文件
│   └── wangxiao_scrapy/
│       ├── __init__.py
│       ├── items.py                # 数据项定义
│       ├── middlewares.py          # 中间件
│       ├── pipelines.py            # 数据管道
│       ├── run_spider.py           # Scrapy爬虫运行脚本
│       ├── settings.py             # Scrapy设置
│       ├── spiders/                # 爬虫文件目录
│       └── 运行.py                 # 爬虫运行脚本
└── 💻 webdriver/                      # 浏览器驱动目录
    └── msedgedriver.exe            # Edge浏览器驱动（Windows）
```

### 📋 核心文件说明

#### ⚙️ config.py - 项目核心配置文件
这是项目最重要的文件，所有配置信息都集中在这里：
- 🔐 网校账号密码配置
- 🖼️ 超级鹰验证码服务配置
- 🗄️ Redis和MySQL数据库配置
- 💻 浏览器驱动路径配置
- ⚡ 各种运行参数和超时设置

#### 🔐 cookie_get.py - Cookie获取脚本
- 🔐 用于自动登录网校并获取Cookie
- 🌐 使用Selenium模拟浏览器操作
- 🖼️ 集成超级鹰验证码识别服务
- 💾 获取的Cookie保存到results/cookies/目录

#### 🕷️ run_spider.py - 爬虫主程序
- 🎯 项目的核心爬虫程序
- 🔐 从Cookie文件中读取认证信息
- 📥 执行实际的网页数据爬取
- 🗄️ 将爬取数据暂存到Redis数据库

#### 🛠️ data_tools/ - 数据处理工具
包含多个数据导出工具：
- 📝 redis_to_md.py: 将Redis数据导出为Markdown格式
- 🗄️ redis_to_mysql.py: 将Redis数据导入MySQL数据库

## ⚙️ 环境配置

### 1️⃣ Python环境配置

确保已安装<kbd>Python 3.10+</kbd>，在命令行中检查Python版本：

```bash
python --version
```

### 2️⃣ 安装项目依赖

在项目根目录下运行以下命令安装所有依赖包：

```bash
pip install -r requirements.txt
```

如果未安装pip，请先安装pip后再执行上述命令。

### 3️⃣ 数据库配置

#### 🗄️ Redis配置
- ✅ 确保Redis服务已安装并正在运行
- 🌐 默认连接地址为 localhost:6379
- ⚙️ 如需修改，请在 `config.py` 中调整Redis连接参数

#### 🗄️ MySQL配置（如需要）
- ✅ 确保MySQL服务已安装并正在运行
- 🔐 创建数据库并设置用户名密码
- ⚙️ 在 `config.py` 中配置MySQL连接参数

### 4️⃣ 配置文件设置

编辑 `config.py` 文件，按以下说明配置各项参数：

#### 🔐 网站登录配置
- `USERNAME`: 网校登录账号（必填）
- `PASSWORD`: 网校登录密码（必填）
- `LOGIN_URL`: 登录页面URL（一般无需修改）

#### 🖼️ 超级鹰配置（验证码识别服务）
- `CHAOJIYING_USERNAME`: 超级鹰用户名（必填）
- `CHAOJIYING_PASSWORD`: 超级鹰密码（必填）
- `CHAOJIYING_SOFT_ID`: 软件ID（必填）
- `CHAOJIYING_CODE_TYPE`: 验证码类型（一般为8001，无需修改）

#### 💻 Selenium浏览器配置
- `DRIVER_PATH`: 浏览器驱动路径（重要！）
  - 💻 Windows用户：确保webdriver文件夹中有msedgedriver.exe

#### 🗄️ Redis数据库配置
- `REDIS_HOST`: Redis服务器地址（默认localhost）
- `REDIS_PORT`: Redis端口（默认6379）
- `REDIS_DB`: Redis数据库编号（默认5）
- `REDIS_PARAMS['password']`: Redis密码（如需要）

#### 🗄️ MySQL数据库配置
- `MYSQL_CONFIG['host']`: MySQL服务器地址
- `MYSQL_CONFIG['user']`: MySQL用户名
- `MYSQL_CONFIG['password']`: MySQL密码
- `MYSQL_CONFIG['database']`: MySQL数据库名
- `MYSQL_CONFIG['charset']`: 字符集（一般为utf8mb4）

#### 💻 浏览器窗口设置
- `WINDOW_WIDTH`: 窗口宽度（默认1920）
- `WINDOW_HEIGHT`: 窗口高度（默认1080）

#### ⚙️ 运行参数配置
- `RUN_INTERVAL_HOURS`: Cookie获取频率（单位：小时）
- `MAX_RETRIES`: 失败重试次数
- `RETRY_DELAY`: 重试等待时间（单位：秒）

#### ⏱️ 超时设置
- `PAGE_LOAD_TIMEOUT`: 页面加载超时时间（单位：秒）
- `ELEMENT_WAIT_TIMEOUT`: 元素等待超时时间（单位：秒）
- `IMPLICIT_WAIT`: 隐式等待时间（单位：秒）

## 🚀 项目启动流程

### 1️⃣ 配置项目
确保已正确配置 `config.py` 文件，填入所有必需的数据库连接信息和账户密码。

### 2️⃣ 获取Cookie
运行 `cookie_get.py` 获取必要的登录Cookie，这是访问受保护页面的关键步骤：

```bash
python cookie_get.py
```

✅ 运行成功后，Cookie信息将保存到 `results/cookies/` 目录中。

### 3️⃣ 启动爬虫
运行 `run_spider.py` 开始爬取数据：

```bash
python run_spider.py
```

`run_spider.py` 是爬虫的主程序，负责执行数据爬取任务。爬取的数据将暂时存储在Redis中。

## ❓ 常见问题解答

### Q1: 运行时提示找不到浏览器驱动怎么办？
**A:** 请检查 `webdriver/` 目录下是否有对应的浏览器驱动文件（如msedgedriver.exe或chromedriver.exe），并在 `config.py` 中正确设置 `DRIVER_PATH` 参数。

### Q2: 验证码识别失败怎么办？
**A:** 请确保超级鹰配置正确，账户余额充足。如果仍有问题，可以尝试更换验证码类型或联系超级鹰客服。

### Q3: Cookie获取失败怎么办？
**A:** 请检查网络连接、账号密码是否正确，以及网站是否更改了登录方式。可以尝试手动登录网站验证。

### Q4: 爬虫运行缓慢怎么办？
**A:** 可以调整 `config.py` 中的超时设置参数，或检查网络连接速度。同时确保数据库服务正常运行。

### Q5: 如何查看爬取的数据？
**A:** 爬取的数据会暂存在Redis中，可以使用data_tools目录下的工具将数据导出为Markdown或MySQL格式。

## 📋 数据导出

爬取的数据存储在Redis中，可以使用以下工具导出：

### 导出到Markdown文件
```bash
python data_tools/redis_to_md.py
```

### 导出到MySQL数据库
```bash
python data_tools/redis_to_mysql.py
```

## ⚠️ 法律法规提醒

本项目仅供学习交流使用，请遵守相关法律法规，合理使用网络爬虫技术，尊重网站的robots.txt协议，避免对目标网站造成过大压力。

## 数据处理

项目提供数据处理工具位于 `data_tools/` 文件夹中：

### redis_to_md.py
从Redis数据库中提取已爬取的数据，并保存为Markdown格式文件到 `results/q_all/` 目录中。

使用方法：
```bash
python data_tools/redis_to_md.py
```

### redis_to_mysql.py
将Redis中的数据迁移到MySQL数据库中，便于数据管理和查询。

使用方法：
```bash
python data_tools/redis_to_mysql.py
```

## 结果存储

- 爬取的问题数据默认存储在 `results/q_all/` 目录
- Cookie信息存储在 `results/cookies/` 目录
- 日志文件存储在 `results/logs/` 目录
- 验证码图片临时存储在 `results/captchas/` 目录

## 常见问题

### 1. 依赖包安装失败
- 确保网络连接正常
- 尝试使用国内镜像源安装：
  ```bash
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
  ```

### 2. Redis连接失败
- 检查Redis服务是否已启动
- 检查 `config.py` 中的Redis配置是否正确

### 3. MySQL连接失败
- 检查MySQL服务是否已启动
- 检查 `config.py` 中的MySQL配置是否正确
- 确认数据库用户权限设置

### 4. Cookie获取失败
- 检查 `config.py` 中的账户密码是否正确
- 确认目标网站账号是否有效
- 检查网络连接是否正常

## 注意事项

1. 请确保在运行项目前已正确配置 `config.py` 文件
2. 需要安装项目依赖：`pip install -r requirements.txt`
3. 确保Redis和MySQL服务已启动并可连接
4. 根据需要调整爬取频率，避免对目标网站造成过大压力

5. 遵守网站的robots.txt协议和相关法律法规
