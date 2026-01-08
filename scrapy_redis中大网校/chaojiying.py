#!/usr/bin/env python
# coding:utf-8
"""
超级鹰验证码识别客户端
官方文档：http://www.chaojiying.com/api-14.html
"""
import requests
from hashlib import md5


class ChaojiyingClient:
    """超级鹰验证码识别客户端"""

    def __init__(self, username, password, soft_id):
        """
        初始化客户端
        :param username: 超级鹰用户名
        :param password: 超级鹰密码
        :param soft_id: 软件ID（用户中心获取）
        """
        self.username = username
        password = password.encode('utf8')
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def recognize_from_file(self, image_path, codetype=8001):
        """
        从图片文件识别验证码
        :param image_path: 图片文件路径
        :param codetype: 验证码类型，默认8001
        :return: 识别结果字典
        """
        try:
            with open(image_path, 'rb') as f:
                im = f.read()
            return self.recognize_from_bytes(im, codetype)
        except FileNotFoundError:
            return {
                'err_no': -2,
                'err_str': f'文件不存在: {image_path}',
                'pic_id': '',
                'pic_str': '',
                'md5': ''
            }
        except Exception as e:
            return {
                'err_no': -3,
                'err_str': f'读取文件失败: {str(e)}',
                'pic_id': '',
                'pic_str': '',
                'md5': ''
            }

    def recognize_from_bytes(self, image_bytes, codetype=8001):
        """
        从字节数据识别验证码
        :param image_bytes: 图片字节数据
        :param codetype: 验证码类型
        :return: 识别结果字典
        """
        params = {'codetype': codetype}
        params.update(self.base_params)
        files = {'userfile': ('captcha.jpg', image_bytes)}

        try:
            response = requests.post(
                'http://upload.chaojiying.net/Upload/Processing.php',
                data=params,
                files=files,
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except requests.exceptions.Timeout:
            return {
                'err_no': -4,
                'err_str': '请求超时',
                'pic_id': '',
                'pic_str': '',
                'md5': ''
            }
        except Exception as e:
            return {
                'err_no': -1,
                'err_str': str(e),
                'pic_id': '',
                'pic_str': '',
                'md5': ''
            }

    def recognize_from_base64(self, base64_str, codetype=8001):
        """
        从base64字符串识别验证码
        :param base64_str: base64编码的图片数据
        :param codetype: 验证码类型
        :return: 识别结果字典
        """
        params = {
            'codetype': codetype,
            'file_base64': base64_str
        }
        params.update(self.base_params)

        try:
            response = requests.post(
                'http://upload.chaojiying.net/Upload/Processing.php',
                data=params,
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {
                'err_no': -1,
                'err_str': str(e),
                'pic_id': '',
                'pic_str': '',
                'md5': ''
            }

    def report_error(self, pic_id):
        """
        报告识别错误（扣题）
        :param pic_id: 图片ID
        :return: 响应结果
        """
        params = {'id': pic_id}
        params.update(self.base_params)

        try:
            response = requests.post(
                'http://upload.chaojiying.net/Upload/ReportError.php',
                data=params,
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {'err_no': -1, 'err_str': str(e)}


# 独立测试代码（不依赖config.py）
if __name__ == '__main__':
    print("=" * 60)
    print("超级鹰客户端测试")
    print("=" * 60)

    # 测试配置（可以直接在这里修改）
    test_config = {
        'username': 'slli123829',  # 修改为你的用户名
        'password': '0p3q5dkw',  # 修改为你的密码
        'soft_id': '976725',  # 修改为你的软件ID
        'code_type': '8001'
    }

    # 创建客户端
    client = ChaojiyingClient(
        test_config['username'],
        test_config['password'],
        test_config['soft_id']
    )

    print(f"客户端创建成功")
    print(f"用户名: {test_config['username']}")
    print(f"软件ID: {test_config['soft_id']}")
    print(f"验证码类型: {test_config['code_type']}")

    # 测试识别
    test_image = "./results/captcha_temp.jpg"  # 默认测试图片路径
    import os

    if os.path.exists(test_image):
        print(f"\n测试识别图片: {test_image}")
        result = client.recognize_from_file(test_image, test_config['code_type'])

        print(f"识别结果: {result}")
        if result['err_no'] == 0:
            print(f"✅ 验证码识别成功: {result['pic_str']}")
            print(f"图片ID: {result['pic_id']}")
        else:
            print(f"❌ 识别失败: {result['err_str']}")
    else:
        print(f"\n⚠ 测试图片不存在: {test_image}")
        print("请先运行 cookie_get.py 生成验证码图片")

    print("=" * 60)