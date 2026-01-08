import redis
import json
import re
import pymysql
from typing import List, Dict
from config import (
    # Redis配置
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PARAMS,
    # mysql配置
    MYSQL_CONFIG
)

class SimpleMySQLStorage:

    def __init__(self):
        # Redis连接
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,password=REDIS_PARAMS['password'], db=REDIS_DB, decode_responses=True)
        self.redis_key = 'questions:items'

        # MySQL连接配置
        self.mysql_config = MYSQL_CONFIG
        # 创建MySQL连接
        self.db = pymysql.connect(**self.mysql_config)
        self.cursor = self.db.cursor()

        # 创建表
        self.create_table()

    def create_table(self):
        """创建数据库表"""
        sql = """
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            path TEXT COMMENT '文件路径，用->连接',
            content TEXT COMMENT '题目内容（保留img标签）',
            options TEXT COMMENT '选项，JSON格式',
            answer VARCHAR(50) COMMENT '答案',
            analysis TEXT COMMENT '答案解析（保留img标签）',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        try:
            self.cursor.execute(sql)
            self.db.commit()
            print("✅ 表创建成功")
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            self.db.rollback()

    def clean_content(self, html: str) -> str:
        """清理题目内容：去掉HTML标签但保留img标签"""
        if not html:
            return ""

        # 去掉<p>标签，但保留内容
        html = html.replace('<p>', '').replace('</p>', '')

        # 去掉除了img之外的所有HTML标签
        # 这个方法保留img标签及其属性
        result = ''
        i = 0
        while i < len(html):
            if html[i] == '<':
                # 检查是否是img标签
                if html[i:i + 4].lower() == '<img':
                    # 保留完整的img标签
                    end = html.find('>', i)
                    if end != -1:
                        result += html[i:end + 1]
                        i = end + 1
                    else:
                        i += 1
                else:
                    # 跳过其他标签
                    end = html.find('>', i)
                    if end != -1:
                        i = end + 1
                    else:
                        i += 1
            else:
                result += html[i]
                i += 1

        # 清理多余的空格
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    def extract_answer(self, analysis: str) -> str:
        """从解析中提取答案"""
        if not analysis:
            return ""

        # 找<p>前面的字母或数字
        # 比如 "B<p>..." 或 "1<p>..."
        match = re.match(r'^([A-Z0-9]+)<p>', analysis)
        if match:
            answer = match.group(1)
            # 如果是数字，处理判断题
            if answer.isdigit():
                if answer == '1':
                    return '正确'
                elif answer == '0':
                    return '错误'
            return answer

        # 如果没有<p>标签，直接取开头的字母或数字
        match = re.match(r'^([A-Z0-9]+)', analysis)
        if match:
            answer = match.group(1)
            if answer.isdigit():
                if answer == '1':
                    return '正确'
                elif answer == '0':
                    return '错误'
            return answer

        return ""

    def clean_analysis(self, analysis: str) -> str:
        """清理答案解析：保留img标签"""
        if not analysis:
            return ""

        # 去掉开头的答案部分
        # 比如 "B<p>内容..." 变成 "内容..."
        analysis = re.sub(r'^[A-Z0-9]+<p>', '', analysis)

        # 去掉<p>标签，但保留内容
        analysis = analysis.replace('<p>', '').replace('</p>', '')

        # 保留img标签（和方法clean_content一样）
        result = ''
        i = 0
        while i < len(analysis):
            if analysis[i] == '<':
                # 检查是否是img标签
                if analysis[i:i + 4].lower() == '<img':
                    # 保留完整的img标签
                    end = analysis.find('>', i)
                    if end != -1:
                        result += analysis[i:end + 1]
                        i = end + 1
                    else:
                        i += 1
                else:
                    # 跳过其他标签
                    end = analysis.find('>', i)
                    if end != -1:
                        i = end + 1
                    else:
                        i += 1
            else:
                result += analysis[i]
                i += 1

        result = result.strip()

        return result

    def process_single(self, item: Dict) -> Dict:
        """处理单个数据"""
        result = {}

        # 1. 处理path：用->连接
        path_list = item.get('path', [])
        result['path'] = '->'.join(path_list) if path_list else ''

        # 2. 处理content：去掉HTML标签但保留img
        content = item.get('content', '')
        result['content'] = self.clean_content(content)

        # 3. 处理options：原样保存（JSON格式）
        options = item.get('options', [])
        result['options'] = json.dumps(options, ensure_ascii=False) if options else '[]'

        # 4. 处理textAnalysis
        analysis = item.get('textAnalysis', '')
        # 提取答案
        result['answer'] = self.extract_answer(analysis)
        # 清理解析（保留img）
        result['analysis'] = self.clean_analysis(analysis)

        return result

    def save_to_mysql(self, data: Dict):
        """保存到MySQL"""
        sql = """
        INSERT INTO questions (path, content, options, answer, analysis)
        VALUES (%s, %s, %s, %s, %s)
        """

        try:
            self.cursor.execute(sql, (
                data['path'],
                data['content'],
                data['options'],
                data['answer'],
                data['analysis']
            ))
            self.db.commit()
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            self.db.rollback()
            return False

    def process_all(self, limit=None):
        """处理所有数据"""
        print("🚀 开始处理数据...")

        # 获取数据总数
        total = self.redis.llen(self.redis_key)
        print(f"📊 Redis中共有 {total} 条数据")

        if limit:
            total = min(total, limit)

        success_count = 0
        fail_count = 0
        discard_count = 0

        for i in range(total):
            try:
                # 读取数据
                item_json = self.redis.lindex(self.redis_key, i)
                if not item_json:
                    continue

                item = json.loads(item_json)

                # 跳过无效数据（没有content或textAnalysis）
                if not item.get('content') or not item.get('textAnalysis'):
                    discard_count += 1
                    continue

                # 处理数据
                cleaned_data = self.process_single(item)

                # 保存到MySQL
                if self.save_to_mysql(cleaned_data):
                    success_count += 1
                else:
                    fail_count += 1

                # 显示进度
                if (i + 1) % 100 == 0:
                    print(f"🔄 已处理 {i + 1}/{total} 条，成功: {success_count}，失败: {fail_count},过滤: {discard_count}")

            except Exception as e:
                print(f"❌ 处理第{i}条数据失败: {e}")
                fail_count += 1

        print("=" * 50)
        print(f"🎉 处理完成！")
        print(f"✅ 成功: {success_count} 条")
        print(f"❌ 失败: {fail_count} 条")

    def close(self):
        """关闭连接"""
        self.cursor.close()
        self.db.close()
        print("✅ 连接已关闭")


# 测试函数
def test_clean_functions():
    """测试清洗函数"""
    processor = SimpleMySQLStorage()

    # 测试数据
    test_cases = [
        {
            'content': '<p>题目内容<img src="http://img.wangxiao.cn/bjupload/2020-10-29/53f7a0c0-57de-45d4-aef7-e8137f5309e4.png" alt="图片">更多内容</p>',
            'analysis': 'B<p>解析内容<img src="http://img.wangxiao.cn/bjupload/2019-08-29/b1f990aa-a6a9-43dc-8807-3284ab9a36e9.png">更多解析</p>'
        },
        {
            'content': '<p>只有文字没有图片</p>',
            'analysis': 'A<p>纯文字解析</p>'
        },
        {
            'content': '<img src="http://img.wangxiao.cn/bjupload/2019-08-29/b1f990aa-a6a9-43dc-8807-3284ab9a36e9.png"><p>图片在前</p>',
            'analysis': '1<p>判断题解析</p>'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原始content: {test['content']}")
        print(f"清洗后content: {processor.clean_content(test['content'])}")
        print(f"提取答案: {processor.extract_answer(test['analysis'])}")
        print(f"清洗后analysis: {processor.clean_analysis(test['analysis'])}")

    processor.close()


# 使用示例
if __name__ == '__main__':
    # 先测试清洗函数
    # print("🧪 测试清洗函数...")
    # test_clean_functions()
    #
    # print("\n" + "=" * 50 + "\n")

    # 运行实际处理
    processor = SimpleMySQLStorage()

    # 处理数据（参数：处理多少条，None表示全部）
    # processor.process_all(limit=1000)  # 先测试1000条
    # 全部
    processor.process_all(limit=None)  # 存储全部
    # 关闭连接
    processor.close()