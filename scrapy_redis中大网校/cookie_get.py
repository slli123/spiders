import time
import json
import logging
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# ==================== 导入统一配置 ====================
try:
    # 基础配置
    from config import (
        # 登录账号
        USERNAME, PASSWORD, LOGIN_URL,

        # 超级鹰配置
        CHAOJIYING_USERNAME, CHAOJIYING_PASSWORD,
        CHAOJIYING_SOFT_ID, CHAOJIYING_CODE_TYPE,

        # 路径配置
        DRIVER_PATH, COOKIE_LATEST_FILE, CAPTCHA_TEMP_FILE,
        LOG_FILE, SCREENSHOTS_DIR,

        # 运行参数
        RUN_INTERVAL_HOURS, MAX_RETRIES, RETRY_DELAY,
        PAGE_LOAD_TIMEOUT, ELEMENT_WAIT_TIMEOUT, IMPLICIT_WAIT,

        # 元素定位
        LOGIN_ELEMENTS,

        # 浏览器设置
        WINDOW_WIDTH, WINDOW_HEIGHT,

        # 目录路径
        RESULTS_DIR, COOKIES_DIR, CAPTCHA_DIR,
    )

    # 导入超级鹰客户端
    from chaojiying import ChaojiyingClient

except ImportError as e:
    print(f"❌ 导入配置失败: {e}")
    print("请确保存在 config.py 和 chaojiying.py 文件")
    print("运行 'python config.py' 检查配置")
    exit(1)

# ==================== 日志配置 ====================
# 使用配置文件中的日志路径
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CookieFetcher:
    """Cookie获取器 - 使用超级鹰"""

    def __init__(self):
        self.driver = None
        self.original_login_url = LOGIN_URL

        # 初始化超级鹰客户端
        self.cjy_client = ChaojiyingClient(
            CHAOJIYING_USERNAME,
            CHAOJIYING_PASSWORD,
            CHAOJIYING_SOFT_ID
        )
        logger.info("超级鹰客户端初始化完成")

    def setup_driver(self):
        """初始化浏览器"""
        options = Options()

        # 反检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")

        # 是否无头模式
        # if HEADLESS:
        #     options.add_argument("--headless")
        #     options.add_argument("--disable-gpu")

        # 窗口大小
        options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")

        # 允许图片加载（验证码需要）
        prefs = {"profile.default_content_setting_values.images": 1}
        options.add_experimental_option("prefs", prefs)

        # 初始化驱动
        service = Service(executable_path=DRIVER_PATH)
        self.driver = webdriver.Edge(service=service, options=options)

        # 设置超时
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.driver.implicitly_wait(IMPLICIT_WAIT)

        logger.info("浏览器初始化完成")

    def wait_for_element(self, xpath, timeout=None, check_interval=0.5):
        """等待元素出现"""
        if timeout is None:
            timeout = ELEMENT_WAIT_TIMEOUT

        start = time.time()
        while time.time() - start < timeout:
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                if element.is_displayed():
                    # 找到元素后额外等待1秒，确保稳定
                    time.sleep(1)
                    return element
            except:
                pass
            time.sleep(check_interval)

        logger.warning(f"元素等待超时 ({timeout}s): {xpath}")
        return None

    def wait_for_image_loaded(self, img_element, timeout=10):
        """等待图片加载完成"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                # 检查图片是否真正加载完成
                is_complete = self.driver.execute_script(
                    "return arguments[0].complete && arguments[0].naturalWidth > 0",
                    img_element
                )
                if is_complete:
                    logger.info("验证码图片已加载完成")
                    return True
            except:
                pass
            time.sleep(0.5)

        logger.warning("图片加载超时")
        return False

    def recognize_captcha_cjy(self, image_path):
        """
        使用超级鹰识别验证码
        :param image_path: 验证码图片路径
        :return: (captcha_text, pic_id) or (None, None)
        """
        try:
            logger.info(f"调用超级鹰识别验证码: {image_path}")

            # 调用超级鹰API
            result = self.cjy_client.recognize_from_file(image_path, CHAOJIYING_CODE_TYPE)

            # 检查返回结果
            if result.get('err_no') == 0:
                captcha_text = result.get('pic_str', '').strip()
                pic_id = result.get('pic_id', '')

                if captcha_text:
                    logger.info(f"超级鹰识别成功: {captcha_text} (ID: {pic_id})")
                    return captcha_text, pic_id
                else:
                    logger.warning("超级鹰返回空验证码")
            else:
                error_msg = result.get('err_str', '未知错误')
                logger.error(f"超级鹰识别失败: {error_msg}")

        except Exception as e:
            logger.error(f"调用超级鹰异常: {e}")

        return None, None

    def report_captcha_error(self, pic_id):
        """报告验证码识别错误（扣题）"""
        if not pic_id:
            return

        try:
            result = self.cjy_client.report_error(pic_id)
            if result.get('err_no') == 0:
                logger.info(f"已报告错误验证码 ID: {pic_id}")
            else:
                logger.warning(f"报告错误失败: {result.get('err_str')}")
        except Exception as e:
            logger.error(f"报告错误异常: {e}")

    def process_captcha(self):
        """处理验证码（使用超级鹰）"""
        logger.info("开始处理验证码...")

        # 使用配置文件中的XPath
        captcha_xpath = LOGIN_ELEMENTS["captcha_image"]

        # 1. 找到验证码图片元素
        captcha_img = self.wait_for_element(captcha_xpath, timeout=8)
        if not captcha_img:
            logger.error(f"找不到验证码图片: {captcha_xpath}")
            return None, None, None

        # 2. 等待图片加载完成
        if not self.wait_for_image_loaded(captcha_img):
            logger.warning("图片可能未完全加载，继续尝试...")

        # 3. 使用配置文件中的验证码临时文件路径
        captcha_path = CAPTCHA_TEMP_FILE

        try:
            captcha_img.screenshot(captcha_path)
            logger.info(f"验证码截图保存到: {captcha_path}")
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None, None, None

        # 4. 调用超级鹰识别
        captcha_text, pic_id = self.recognize_captcha_cjy(captcha_path)

        return captcha_text, pic_id, captcha_path

    def smart_login_check(self):
        """智能登录检测"""
        try:
            current_url = self.driver.current_url.lower()
            logger.info(f"当前URL: {current_url[:100]}")

            # URL检测
            login_keywords = ["login", "signin", "登录", "auth", "authenticate"]
            for keyword in login_keywords:
                if keyword in current_url:
                    logger.warning(f"URL中包含登录关键词: {keyword}")

            # 页面元素检测 - 查找登录失败提示
            failure_patterns = ['账号或密码错误', '验证码错误', '登录失败', '不正确']
            for pattern in failure_patterns:
                try:
                    elements = self.driver.find_elements(
                        By.XPATH, f'//*[contains(text(), "{pattern}")]'
                    )
                    for elem in elements[:2]:
                        if elem.text and len(elem.text.strip()) > 0:
                            logger.error(f"检测到失败提示: {elem.text[:50]}")
                            return False
                except:
                    pass

            # 检查是否仍在登录表单
            for key in ["username_input", "password_input", "captcha_input"]:
                try:
                    xpath = LOGIN_ELEMENTS.get(key)
                    if xpath and self.driver.find_elements(By.XPATH, xpath):
                        logger.warning(f"仍检测到登录表单元素: {key}")
                        return False
                except:
                    pass

            # 如果URL没有登录关键词，也没有失败元素，保守判断为成功
            has_login_keyword = any(keyword in current_url for keyword in login_keywords)
            if not has_login_keyword:
                logger.info("URL无登录关键词，登录成功")
                return True

            logger.warning("无法确定登录状态，保守返回失败")
            return False

        except Exception as e:
            logger.error(f"登录检测异常: {e}")
            return False

    def fetch_once(self):
        """单次获取Cookie"""
        try:
            logger.info("=" * 50)
            logger.info("开始获取Cookie")

            self.setup_driver()

            # 1. 访问网站
            self.driver.get(self.original_login_url)
            logger.info(f"访问网站: {self.original_login_url}")
            time.sleep(2)

            # 2. 点击登录（使用配置文件中的XPath）
            login_btn = self.wait_for_element(LOGIN_ELEMENTS["login_button"])
            if not login_btn:
                raise Exception("找不到登录按钮")
            login_btn.click()
            logger.info("点击登录")
            time.sleep(2)

            # 3. 切换到密码登录
            pwd_tab = self.wait_for_element(LOGIN_ELEMENTS["password_tab"])
            if pwd_tab:
                pwd_tab.click()
                logger.info("切换到密码登录")
                time.sleep(2)

            # 4. 处理验证码
            captcha_text, pic_id, captcha_path = self.process_captcha()
            if not captcha_text:
                raise Exception("验证码识别失败")

            # 5. 找到输入框（使用配置文件中的XPath）
            username_input = self.wait_for_element(LOGIN_ELEMENTS["username_input"])
            password_input = self.wait_for_element(LOGIN_ELEMENTS["password_input"])
            captcha_input = self.wait_for_element(LOGIN_ELEMENTS["captcha_input"])

            if not all([username_input, password_input, captcha_input]):
                raise Exception("输入框未全部找到")

            # 6. 输入信息
            logger.info("填写登录信息...")

            # 输入用户名
            ActionChains(self.driver).move_to_element(username_input).click().pause(0.2).send_keys(USERNAME).perform()
            logger.info(f"已输入用户名: {USERNAME}")
            time.sleep(0.5)

            # 输入验证码
            ActionChains(self.driver).move_to_element(captcha_input).click().pause(0.2).send_keys(
                captcha_text).perform()
            logger.info(f"已输入验证码: {captcha_text}")
            time.sleep(0.5)

            # 输入密码
            ActionChains(self.driver).move_to_element(password_input).click().pause(0.2).send_keys(PASSWORD).perform()
            logger.info("已输入密码: ***")
            time.sleep(0.5)

            # 7. 点击登录
            submit_btn = self.wait_for_element(LOGIN_ELEMENTS["submit_button"])
            if submit_btn:
                submit_btn.click()
                logger.info("提交登录")
                time.sleep(3)

            # 8. 智能登录检测
            logger.info("进行智能登录检测...")
            if not self.smart_login_check():
                logger.error("❌ 智能登录检测失败")

                # 如果验证码识别错误，报告错误
                if pic_id:
                    self.report_captcha_error(pic_id)

                raise Exception("登录失败（智能检测未通过）")

            logger.info("✅ 智能登录检测通过")

            # 9. 获取Cookie
            cookies = self.driver.get_cookies()
            logger.info(f"获取到 {len(cookies)} 条Cookie")

            # 10. 保存Cookie
            self.save_cookies(cookies)

            return True

        except Exception as e:
            logger.error(f"获取失败: {e}")

            # 错误截图
            if self.driver:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    error_path = Path(SCREENSHOTS_DIR) / f"error_{timestamp}.png"
                    self.driver.save_screenshot(str(error_path))
                    logger.info(f"错误截图: {error_path}")
                except Exception as screenshot_error:
                    logger.error(f"保存截图失败: {screenshot_error}")

            return False

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("关闭浏览器")
                except:
                    pass

    def save_cookies(self, cookies):
        """保存Cookie为Scrapy-Redis格式"""
        # 转换为字典格式
        cookie_dict = {c["name"]: c["value"] for c in cookies}

        # 带时间戳的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_file = Path(COOKIES_DIR) / f"cookies_{timestamp}.json"

        data = {
            "cookies": cookie_dict,
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "source": "wangxiao.cn",
                "count": len(cookie_dict),
                "username": USERNAME
            }
        }

        # 保存带时间戳的文件
        with open(timestamped_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cookie保存到: {timestamped_file}")

        # 保存最新版本（使用配置文件中的路径）
        with open(COOKIE_LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"最新Cookie: {COOKIE_LATEST_FILE}")

    def run_forever(self):
        """7x24小时运行"""
        logger.info("=" * 60)
        logger.info("🍪 Cookie获取服务启动")
        logger.info(f"运行间隔: {RUN_INTERVAL_HOURS}小时")
        logger.info(f"最大重试: {MAX_RETRIES}次")
        logger.info(f"重试延迟: {RETRY_DELAY}秒")
        logger.info("按 Ctrl+C 停止程序")
        logger.info("=" * 60)

        consecutive_failures = 0

        while True:
            try:
                logger.info(f"开始执行（连续失败次数: {consecutive_failures}）")

                success = False
                for attempt in range(MAX_RETRIES):
                    logger.info(f"第{attempt + 1}次尝试")

                    if self.fetch_once():
                        success = True
                        consecutive_failures = 0
                        break
                    else:
                        if attempt < MAX_RETRIES - 1:
                            wait_time = RETRY_DELAY * (attempt + 1)
                            logger.info(f"{wait_time // 60}分{wait_time % 60}秒后重试...")
                            time.sleep(wait_time)

                if success:
                    # 计算下次执行时间
                    wait_seconds = RUN_INTERVAL_HOURS * 3600
                    next_time = datetime.now().timestamp() + wait_seconds
                    next_str = datetime.fromtimestamp(next_time).strftime("%Y-%m-%d %H:%M:%S")

                    logger.info(f"✅ 本次执行成功！")
                    logger.info(f"⏰ 下次执行时间: {next_str}")

                    # 等待下次执行
                    time.sleep(wait_seconds)
                else:
                    consecutive_failures += 1
                    logger.error(f"❌ 全部尝试失败（连续失败: {consecutive_failures}次）")

                    # 连续失败过多则延长等待
                    if consecutive_failures >= 3:
                        extra_wait = min(consecutive_failures * 3600, 86400)  # 最多24小时
                        logger.warning(f"连续失败过多，额外等待{extra_wait // 3600}小时")
                        time.sleep(extra_wait)
                    else:
                        time.sleep(3600)  # 失败后等待1小时

            except KeyboardInterrupt:
                logger.info("👋 收到中断信号，程序退出")
                break
            except Exception as e:
                logger.error(f"💥 运行异常: {e}")
                time.sleep(300)  # 异常后等待5分钟


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🍪 Cookie获取服务")
    print("📅 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔄 运行间隔:", f"{RUN_INTERVAL_HOURS}小时")
    print("🔍 验证码服务: 超级鹰")
    print("=" * 50 + "\n")

    fetcher = CookieFetcher()
    fetcher.run_forever()