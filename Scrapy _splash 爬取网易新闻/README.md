# Scrapy 爬虫项目：wangyi

本项目是一个使用 Scrapy 框架编写的网络爬虫。

## 1. 项目设置与依赖安装

本项目依赖于一个独立的 Python 虚拟环境。

首先，请确保您已经创建了一个虚拟环境，并且已经安装了项目所需的依赖包。

如果您需要将此项目分享给他人或在另一台电脑上部署，可以运行以下命令来安装 `requirements.txt` 文件中列出的所有依赖：

```bash
pip install -r requirements.txt
```

## 2. Splash 服务安装 (Linux-Docker)

本爬虫依赖于 Splash 服务来渲染动态 JavaScript 页面。您需要在 Linux 环境下使用 Docker 来部署 Splash。

### 第一步：拉取 Splash 镜像

```bash
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/whalebothelmsman/splash:latest
```

### 第二步：重命名镜像 (Tagging)

为了方便后续使用，将拉取的镜像重命名为标准名称 `scrapinghub/splash`。

```bash
sudo docker tag swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/whalebothelmsman/splash:latest scrapinghub/splash
```

### 第三步：启动 Splash 容器

执行以下命令以后台模式启动 Splash 服务，并将容器的 8050 端口映射到主机的 8050 端口。

```bash
# 如果需要 root 权限，请使用 sudo
sudo docker run -d -p 8050:8050 scrapinghub/splash

# 如果当前用户已在 docker 用户组，可省略 sudo
docker run -d -p 8050:8050 scrapinghub/splash
```

### 第四步：验证服务

容器启动后，您可以通过浏览器访问以下地址来验证 Splash 服务是否正常运行：

*   `http://localhost:8050`
*   `http://127.0.0.1:8050`

如果您是在远程 Linux 服务器上部署的，请使用 `ifconfig` 或 `ip addr` 命令查看服务器的 IP 地址，然后通过 `http://<服务器IP地址>:8050` 进行访问。

**重要**：请确保 `settings.py` 文件中的 `SPLASH_URL` 配置指向了您部署的 Splash 服务的正确地址。

## 3. 如何运行爬虫

由于本项目是基于 Scrapy 框架的，不能直接通过 `python` 命令运行。请严格按照以下步骤在终端中启动爬虫。

### 关键步骤：在终端中激活环境

这是运行本项目的核心步骤。由于 Windows PowerShell 的执行策略限制，需要手动激活环境。

1.  **打开一个新终端**
    在 IDE 中 (如 Trae IDE, VS Code) 打开一个新的 PowerShell 终端。

2.  **设置执行策略**
    为了允许终端运行激活脚本，请执行以下命令。此命令仅对当前终端窗口有效，是临时的、安全的。

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    ```

3.  **手动激活环境**
    运行您虚拟环境中的 `activate.ps1` 脚本。请将下面的路径替换为您自己环境的**真实路径**。

    ```powershell
    # 示例路径，请务必替换成您自己的！
    E:\this_learn\spider_bilibili\.venv\Scripts\activate.ps1
    ```
    成功后，您会看到命令行前面出现 `(.venv)` 标志。

### 启动爬虫

在**已经成功激活了环境**的终端中，运行以下命令来启动爬虫：

```bash
# "wyi" 是在 spiders/wyi.py 文件中定义的爬虫名称 (name)
scrapy crawl wyi
```

爬虫将会开始运行，并将爬取过程中的日志信息输出到终端。