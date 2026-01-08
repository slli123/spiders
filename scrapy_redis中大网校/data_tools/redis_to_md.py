import asyncio
import random
import time
import aiohttp
import aiofiles
import redis.asyncio as redis
import json
import re
import os
import atexit
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
from collections import defaultdict
import logging
from config import (
    # Redis配置
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PARAMS,
)
import sys
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class FileWriteQueue:
    """基于文件路径的任务队列"""

    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)
        self.processing = set()

    async def enqueue_write(self, file_path, write_func):
        """将写入任务加入队列"""
        queue = self.queues[file_path]
        await queue.put(write_func)

        # 如果该文件没有正在处理的任务，启动处理
        if file_path not in self.processing:
            self.processing.add(file_path)
            asyncio.create_task(self._process_queue(file_path))

    async def _process_queue(self, file_path):
        """处理特定文件的所有写入任务"""
        queue = self.queues[file_path]

        while not queue.empty():
            write_func = await queue.get()
            try:
                await write_func()
            except Exception as e:
                print(f"写入文件 {file_path} 失败: {e}")
            finally:
                queue.task_done()

        self.processing.remove(file_path)

write_queue = FileWriteQueue()
class AsyncMDExporter:
    """异步保存到Markdown文件"""

    def __init__(self, redis_host=REDIS_HOST, redis_port=REDIS_PORT, redis_db=REDIS_DB):
        # Redis连接将在异步上下文中初始化
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_params = REDIS_PARAMS

        # Redis客户端实例
        self.redis: Optional[redis.Redis] = None
        self.redis_key = 'questions:items'

        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None

        # 限制并发数 - 减小并发以降低文件句柄压力
        self.semaphore = asyncio.Semaphore(10)  # 从30减小到10
        self.file_semaphore = asyncio.Semaphore(20)  # 专门用于文件操作的信号量

        # 添加批处理控制
        self.batch_size = 50  # 每次处理的批次大小

        # 统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'images_downloaded': 0,
            'images_failed': 0
        }

    async def init_redis(self):
        """初始化异步Redis连接"""
        try:
            self.redis = await redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_params.get('password'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            await self.redis.ping()
            logger.info("✅ Redis异步连接成功")
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise

    async def init_session(self):
        """初始化aiohttp会话"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        """关闭所有连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已关闭")

        if self.session:
            await self.session.close()
            logger.info("HTTP会话已关闭")

    async def get_valid_data(self, limit: Optional[int] = None) -> List[Dict]:
        """从Redis获取有效数据（异步版本）"""
        if not self.redis:
            await self.init_redis()

        logger.info("📥 从Redis获取数据...")

        total = await self.redis.llen(self.redis_key)
        logger.info(f"📊 Redis中共有 {total} 条数据")

        if limit:
            total = min(total, limit)

        valid_data = []
        for i in range(total):
            try:
                item_json = await self.redis.lindex(self.redis_key, i)
                if not item_json:
                    continue

                item = json.loads(item_json)

                # 过滤无效数据
                if not item.get('content') or not item.get('textAnalysis'):
                    continue

                if not item.get('path'):
                    continue

                valid_data.append(item)

            except Exception as e:
                logger.warning(f"第{i}条数据解析失败: {e}")
                continue

        logger.info(f"✅ 获取到 {len(valid_data)} 条有效数据")
        return valid_data

    def extract_img_urls(self, text: str) -> List[str]:
        """提取文本中的图片URL"""
        if not text:
            return []

        # 匹配所有img标签的src属性
        pattern = r'src="([^"]+)"'
        urls = re.findall(pattern, text)

        # 过滤并返回
        return [url for url in urls if url.startswith('http')]

    async def download_image(self, img_url: str, save_dir: Path) -> Optional[str]:
        """异步下载单张图片"""
        if not self.session:
            return None

        # 生成文件名
        try:
            filename = img_url.split('/')[-1]
            # 清理文件名（移除查询参数等）
            filename = filename.split('?')[0]

            # 确保是图片文件
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                filename += '.jpg'  # 默认加.jpg扩展名

            save_path = save_dir / filename

            async with self.semaphore:
                try:
                    async with self.session.get(img_url) as response:
                        if response.status == 200:
                            content = await response.read()
                            async with aiofiles.open(save_path, 'wb') as f:
                                await f.write(content)

                            self.stats['images_downloaded'] += 1
                            if self.stats['images_downloaded'] % 10 == 0:
                                logger.info(f"📸 已下载 {self.stats['images_downloaded']} 张图片...")

                            return str(save_path.relative_to(save_dir.parent))
                        else:
                            logger.warning(f"图片下载失败 {img_url}: 状态码 {response.status}")
                except Exception as e:
                    logger.warning(f"图片下载失败 {img_url}: {e}")

        except Exception as e:
            logger.warning(f"处理图片URL失败 {img_url}: {e}")

        self.stats['images_failed'] += 1
        return None

    async def replace_img_urls(self, text: str, img_dir: Path) -> str:
        """替换文本中的图片URL为本地路径"""
        img_urls = self.extract_img_urls(text)

        if not img_urls:
            return text

        # 下载所有图片
        download_tasks = []
        for img_url in img_urls:
            task = self.download_image(img_url, img_dir)
            download_tasks.append((img_url, task))

        # 等待所有下载完成
        results = {}
        for img_url, task in download_tasks:
            local_path = await task
            if local_path:
                results[img_url] = local_path

        # 替换URL
        if results:
            for img_url, local_path in results.items():
                # 替换src属性
                text = text.replace(f'src="{img_url}"', f'src="./{local_path}"')
                # 同时替换没有引号的情况
                text = text.replace(f'src={img_url}', f'src=./{local_path}')

        return text

    def process_answer(self, analysis: str) -> str:
        """处理答案：将开头的数字或字母转换为标准格式"""
        if not analysis:
            return "", analysis

        # 提取开头的答案（字母或数字）
        match = re.match(r'^([A-Z0-9]+)', analysis)
        if not match:
            return "", analysis

        answer = match.group(1)

        # 如果是数字，转换为正确/错误
        if answer.isdigit():
            if answer == '1':
                display_answer = "✅ 正确"
            elif answer == '0':
                display_answer = "❌ 错误"
            else:
                display_answer = f"答案: {answer}"
        else:
            # 字母答案
            if len(answer) == 1:
                display_answer = f"正确答案: {answer}"
            else:
                display_answer = f"正确答案: {', '.join(list(answer))}"

        # 从解析中移除答案部分
        remaining_analysis = analysis[len(answer):]
        # 移除开头的<p>标签（如果有）
        if remaining_analysis.startswith('<p>'):
            remaining_analysis = remaining_analysis[3:]

        return display_answer, remaining_analysis

    def clean_html_for_markdown(self, html: str) -> str:
        """清理HTML，转换为Markdown友好格式"""
        if not html:
            return ""

        # 保留img标签
        html = html.replace('<p>', '').replace('</p>', '')

        # 保留换行
        html = html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')

        # 清理多余的空白
        html = re.sub(r'\s+', ' ', html).strip()

        return html

    def format_question_content(self, content: str) -> str:
        """格式化题目内容，添加高亮效果"""
        highlighted = f'{content}<p style="white-space: normal;">'
        return highlighted

    def format_options(self, options: List[str]) -> str:
        """格式化选项，添加高亮效果"""
        if not options:
            return ""

        formatted_options = []
        for i, option in enumerate(options):
            option = option.strip()
            if not option:
                continue

            formatted = f"{option}"
            formatted_options.append(formatted)

        # 每个选项单独一行，用空行分隔
        return "<br>".join(formatted_options)

    def format_analysis(self, analysis: str) -> str:
        """格式化解析内容"""
        if not analysis:
            return ""

        analysis = self.clean_html_for_markdown(analysis)
        return f"{analysis}"

    def create_markdown_header(self, path: List[str]) -> str:
        """创建Markdown文件头部信息"""
        if len(path) >= 3:
            # 使用最后三层作为标题
            title = " -> ".join(path[-3:])
        else:
            title = " -> ".join(path)

        # 创建带样式的标题
        header = f"""# 📚 {title}

> 分类: {' -> '.join(path)}

---

"""
        return header

    async def save_single_md(self, item: Dict, output_base: Path):
        """保存单个题目为Markdown文件"""
        try:
            # 1. 准备路径且过滤无效
            path = item.get('path', [])
            if len(path) < 3:
                logger.warning(f"路径太短: {path}")
                return False

            # 文件名：最后一层
            filename = path[-1].replace('/', '_').replace('\\', '_')
            if len(filename) > 50:  # 增加文件名长度限制
                filename = filename[:50]
            filename = re.sub(r'[<>:"|?*]', '', filename) + '.md'

            # 保存路径：除最后一层的所有层
            save_dir = output_base
            for part in path[:-1]:
                safe_part = part.replace('/', '_').replace('\\', '_')
                safe_part = re.sub(r'[<>:"|?*]', '', safe_part)
                save_dir = save_dir / safe_part

            # 图片文件夹
            img_dir = save_dir / f"{filename.replace('.md', '_img')}"

            # 创建目录
            save_dir.mkdir(parents=True, exist_ok=True)
            img_dir.mkdir(parents=True, exist_ok=True)

            # 2. 处理数据
            content = item.get('content', '')
            options = item.get('options', [])
            analysis = item.get('textAnalysis', '')

            # 下载并替换图片
            content = await self.replace_img_urls(content, img_dir)
            analysis = await self.replace_img_urls(analysis, img_dir)

            # 处理答案
            answer, clean_analysis = self.process_answer(analysis)

            # 格式化各部分内容
            formatted_content = self.format_question_content(content)
            formatted_options = self.format_options(options)
            formatted_analysis = self.format_analysis(clean_analysis)

            # 3. 写入Markdown文件 - 使用文件信号量控制并发
            md_path = save_dir / filename

            async def actual_write():
                async with self.file_semaphore:  # 控制同时打开的文件数量
                    async with aiofiles.open(md_path, 'a+', encoding='utf-8', errors='replace') as f:
                        # 第一步：将文件指针移到文件开头（解决a+默认指针在末尾的问题）
                        await f.seek(0)
                        # 第二步：异步读取文件内容
                        file_content = await f.read()
                        # time.sleep(random.randint(1, 5))
                        # 第三步：判断内容是否存在，不存在则追加
                        header = self.create_markdown_header(path)
                        if header not in file_content:
                            # 写入文件头部和文件生成时间
                            await f.write(header)
                            await f.write(f"\n*题目保存时间: {self.get_current_time()}*\n")
                            # 添加分隔线和时间戳
                            await f.write("\n")
                            await f.write('---')

                        # 检查内容是否已存在
                        content_check = formatted_content[:100]  # 只检查前100个字符
                        if content_check not in file_content:
                            # 写入题目部分
                            await f.write('\n\n\n---\n')
                            await f.write(f'{formatted_content}')

                            # 写入选项部分
                            if formatted_options:
                                await f.write(f'<p>{formatted_options}</p><p style="white-space: normal;">')

                            # 写入答案部分
                            if answer:
                                await f.write(f'{answer},')

                            # 写入解析部分
                            if formatted_analysis:
                                await f.write(f"{formatted_analysis}<br>")

            await write_queue.enqueue_write(md_path, actual_write)

            self.stats['success'] += 1
            if self.stats['success'] % 100 == 0:
                logger.info(f"✅ 已保存 {self.stats['success']} 个文件...")

            return True

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            self.stats['failed'] += 1
            return False

    def get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def process_batch(self, data: List[Dict], output_base: Path):
        """批量处理数据 - 分批处理避免打开太多文件"""
        logger.info(f"🚀 开始处理 {len(data)} 条数据...")

        # 分批处理
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            logger.info(
                f"📦 处理批次 {i // self.batch_size + 1}/{(len(data) - 1) // self.batch_size + 1} (共 {len(batch)} 条)")

            # 创建任务
            tasks = []
            for item in batch:
                task = self.save_single_md(item, output_base)
                tasks.append(task)

            # 并发执行但等待批次完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 每批处理完后稍作休息
            await asyncio.sleep(0.1)

        logger.info(f"🎉 批量处理完成!")

    async def run(self, limit: Optional[int] = None, output_dir: str = '../results/q_all'):
        """运行完整流程"""
        logger.info("🚀 开始异步导出到Markdown")

        try:
            # 初始化连接
            await self.init_redis()
            await self.init_session()

            # 获取数据
            data = await self.get_valid_data(limit)
            if not data:
                logger.warning("⚠️ 没有获取到有效数据")
                return

            self.stats['total'] = len(data)

            # 创建输出目录
            output_base = Path(output_dir)
            output_base.mkdir(parents=True, exist_ok=True)

            # 处理数据
            await self.process_batch(data, output_base)

            # 打印统计
            logger.info("=" * 50)
            logger.info("📊 最终统计:")
            logger.info(f"  处理总数: {self.stats['total']}")
            logger.info(f"  成功保存: {self.stats['success']}")
            logger.info(f"  保存失败: {self.stats['failed']}")
            logger.info(f"  图片下载: {self.stats['images_downloaded']}")
            logger.info(f"  图片失败: {self.stats['images_failed']}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"❌ 运行失败: {e}")
        finally:
            # 关闭所有连接
            await self.close()


# @atexit.register
def remove_empty_folders_pathlib(path):
    path_obj = Path(path)
    for folder in sorted(path_obj.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
            # print(f"已删除空文件夹: {folder}")

    print("存储结束")


# 快速测试函数
async def test_single_item():
    """测试单个题目处理"""
    exporter = AsyncMDExporter()

    # 测试数据
    test_item = {
        'path': ['税务师', '税法二', '第六章车船税', '第二节征税范围、纳税人和适用税额', '三、税目、税额'],
        'content': '<p>有关船税的计税依据，下列表述正确的有（）。</p>',
        'options': ['A、车辆整备质量尾数在0.5吨以下的不计算车船税', 'B、挂车按载货汽车货车税额的50％计征车船税',
                    'C、已缴纳车船税的车船在同一纳税年度内办理转让过户的，需另行纳税', 'D、非机动驳船，免征车船税'],
        'textAnalysis': 'B<p>如图所示：<img title="1.png" src="http://img.wangxiao.cn/bjupload/2020-10-29/53f7a0c0-57de-45d4-aef7-e8137f5309e4.png" /><br /></p><p>（知识点：税目、税额）</p><p>（题库维护老师：zhx）</p>'}

    # 初始化连接
    await exporter.init_redis()
    await exporter.init_session()

    # 测试保存
    output_base = Path('../results/test_q')
    result = await exporter.save_single_md(test_item, output_base)

    # 预览生成的内容
    if result:
        # 构建正确的文件路径
        safe_filename = test_item['path'][-1].replace('/', '_').replace('\\', '_')
        if len(safe_filename) > 50:
            safe_filename = safe_filename[:50]
        safe_filename = re.sub(r'[<>:"|?*]', '', safe_filename) + '.md'

        # 构建目录路径
        save_dir = output_base
        for part in test_item['path'][:-1]:
            safe_part = part.replace('/', '_').replace('\\', '_')
            safe_part = re.sub(r'[<>:"|?*]', '', safe_part)
            save_dir = save_dir / safe_part

        md_path = save_dir / safe_filename

        if md_path.exists():
            print("\n" + "=" * 50)
            print("📄 生成的Markdown内容预览:")
            print("=" * 50)
            async with aiofiles.open(md_path, 'r', encoding='utf-8', errors='replace') as f:
                content = await f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
            print("=" * 50)

    print(f"\n测试结果: {'成功' if result else '失败'}")

    await exporter.close()


# 主函数
async def main():


    # 解析参数
    limit = None
    output_dir = '../results/q_all'
    atexit.register(remove_empty_folders_pathlib, output_dir)
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"将处理前 {limit} 条数据")
        except ValueError:
            print(f"无效的限制参数: {sys.argv[1]}")

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    print(f"输出目录: {output_dir}")
    print("=" * 50)

    # 创建导出器
    exporter = AsyncMDExporter()

    # 运行导出
    await exporter.run(limit=limit, output_dir=output_dir)

    print("\n🎉 导出完成！")


if __name__ == '__main__':
    # 运行测试函数
    # print("🧪 先运行测试...")
    # asyncio.run(test_single_item())
    #
    # print("\n" + "=" * 50)

    print("🚀 开始主程序...")
    print("=" * 50)

    # 询问是否继续
    response = input("\n是否把redis数据库的数据保存为相应的Markdown文件(y/n): ").strip().lower()
    if response == 'y':
        # 运行主函数
        asyncio.run(main())
    else:
        print("程序退出")