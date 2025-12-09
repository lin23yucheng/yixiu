import threading
import os
import tempfile
import shutil
import logging
import time
import subprocess
from threading import local
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
import urllib3

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(thread)d - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== 并行限流配置 ==========
MAX_BROWSER_INSTANCES = 2  # 先降低并发数，适配版本问题
browser_semaphore = threading.Semaphore(MAX_BROWSER_INSTANCES)
RETRY_TIMES = 2  # 降低重试次数，避免无意义重试
RETRY_DELAY = 3


# ========== 新增：查找Chrome二进制文件 ==========
def find_chrome_binary():
    """
    查找系统上的Chrome或Chromium二进制文件路径
    返回找到的路径，如果未找到则返回None
    """
    # 常见的Chrome/Chromium安装路径
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/opt/google/chrome/google-chrome",
        "/usr/local/bin/chromium",
        "/usr/local/bin/chromium-browser",
    ]

    for path in chrome_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            logger.info(f"找到Chrome二进制文件: {path}")
            return path

    # 使用which命令查找
    try:
        for binary in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            result = subprocess.run(
                ["which", binary],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                if path and os.path.exists(path):
                    logger.info(f"通过which找到Chrome二进制文件: {path}")
                    return path
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    logger.warning("未找到Chrome或Chromium二进制文件")
    return None


# ========== 新增：修复版本检查函数 ==========
def check_chrome_version():
    """检查Chrome和ChromeDriver版本是否匹配"""
    try:
        # 查找Chrome二进制文件
        chrome_bin = find_chrome_binary()
        if not chrome_bin:
            logger.warning("未找到Chrome浏览器")
            return False

        # 获取Chrome版本
        chrome_version = subprocess.check_output(
            [chrome_bin, "--version"],
            stderr=subprocess.STDOUT,
            timeout=10
        ).decode().strip()

        # 解析版本号（处理不同输出格式）
        if "Google Chrome" in chrome_version:
            chrome_main_version = chrome_version.split()[2].split('.')[0]
        else:
            chrome_main_version = chrome_version.split()[1].split('.')[0]

        logger.info(f"Chrome版本: {chrome_version}, 主版本: {chrome_main_version}")

        # 获取ChromeDriver版本
        chromedriver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]

        chromedriver_bin = None
        for path in chromedriver_paths:
            if os.path.exists(path):
                chromedriver_bin = path
                break

        if not chromedriver_bin:
            logger.warning("未找到ChromeDriver")
            return False

        chromedriver_version = subprocess.check_output(
            [chromedriver_bin, "--version"],
            stderr=subprocess.STDOUT,
            timeout=10
        ).decode().strip()

        # 解析ChromeDriver版本号
        chromedriver_main_version = chromedriver_version.split()[1].split('.')[0]

        logger.info(f"ChromeDriver版本: {chromedriver_version}, 主版本: {chromedriver_main_version}")

        # 检查版本是否匹配（允许主版本号一致）
        if chrome_main_version != chromedriver_main_version:
            logger.warning(
                f"版本不匹配！Chrome主版本: {chrome_main_version}, ChromeDriver主版本: {chromedriver_main_version}")
            # 这里不返回False，因为有时版本不匹配也能工作
            return True  # 改为返回True，不因版本不匹配而阻止启动

        logger.info(f"版本匹配：Chrome {chrome_main_version} ↔ ChromeDriver {chromedriver_main_version}")
        return True
    except Exception as e:
        logger.error(f"检查Chrome版本失败: {str(e)}")
        # 即使检查失败也继续执行
        return True


def fix_chromedriver_permission():
    """修复ChromeDriver可执行权限"""
    try:
        chromedriver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]

        for path in chromedriver_paths:
            if os.path.exists(path):
                os.chmod(path, 0o755)  # 赋予可执行权限
                logger.info(f"ChromeDriver权限已设置为755: {path}")
                return

        logger.warning("未找到ChromeDriver文件，无法设置权限")
    except Exception as e:
        logger.error(f"修复ChromeDriver权限失败: {str(e)}")


# ======================================================

class BrowserPool:
    _thread_local = local()

    @classmethod
    def driver(cls):
        """获取当前线程的浏览器实例（带版本检查）"""
        # 首次启动时检查版本
        if not hasattr(cls, '_version_checked'):
            cls._version_checked = True
            check_chrome_version()
            fix_chromedriver_permission()

        if not hasattr(cls._thread_local, 'driver'):
            with browser_semaphore:
                cls._thread_local.driver = cls._create_driver_with_retry()
        return cls._thread_local.driver

    @classmethod
    def _create_driver_with_retry(cls):
        """带重试的driver创建"""
        for retry in range(RETRY_TIMES):
            try:
                return cls._create_driver()
            except (WebDriverException, TimeoutException, urllib3.exceptions.ReadTimeoutError) as e:
                logger.error(f"线程 {threading.get_ident()} 第{retry + 1}次创建浏览器失败: {str(e)}")
                if retry == RETRY_TIMES - 1:
                    raise
                time.sleep(RETRY_DELAY)
        raise Exception(f"线程 {threading.get_ident()} 超出{RETRY_TIMES}次重试，创建浏览器失败")

    @classmethod
    def _create_driver(cls):
        """优化ChromeDriver启动逻辑（移除冲突参数）"""
        logger.info(f"线程 {threading.get_ident()} 开始创建浏览器实例")

        chrome_options = Options()

        # ========== 核心参数：仅保留必需项，移除冲突参数 ==========
        # 必加参数（容器+无头）
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # 轻量化参数（仅保留关键）
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")

        # 屏蔽自动化（简化参数）
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # 页面加载策略（减少超时）
        chrome_options.page_load_strategy = 'eager'

        # ========== 新增：设置Chrome二进制文件路径 ==========
        chrome_binary = find_chrome_binary()
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            logger.info(f"使用Chrome路径: {chrome_binary}")
        else:
            logger.warning("未找到Chrome二进制文件，使用默认路径")
        # ======================================================

        # ========== ChromeDriver服务：简化配置，移除日志参数 ==========
        # 移除verbose/log参数，避免ChromeDriver启动冲突
        try:
            service = Service(executable_path="/usr/local/bin/chromedriver")
        except Exception as e:
            logger.warning(f"线程 {threading.get_ident()} 使用默认chromedriver路径: {str(e)}")
            service = Service()
        # ======================================================

        # 创建driver（增加启动超时）
        try:
            # 新增：设置ChromeDriver启动超时
            service.start_timeout = 30  # 启动超时30秒
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 超时配置
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)
            driver.implicitly_wait(15)

            # 屏蔽webdriver（简化重试）
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info(f"线程 {threading.get_ident()} 浏览器实例创建成功")
            return driver
        except (WebDriverException, TimeoutException) as e:
            logger.error(f"线程 {threading.get_ident()} 创建浏览器失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"线程 {threading.get_ident()} 创建浏览器失败: {str(e)}")
            raise

    @classmethod
    def cleanup(cls):
        """清理浏览器资源"""
        if hasattr(cls._thread_local, 'driver'):
            driver = cls._thread_local.driver
            try:
                logger.info(f"线程 {threading.get_ident()} 开始释放浏览器实例")
                driver.quit()
                logger.info(f"线程 {threading.get_ident()} 浏览器实例释放成功")
            except Exception as e:
                logger.error(f"线程 {threading.get_ident()} 释放浏览器异常: {str(e)}")
            finally:
                del cls._thread_local.driver
                browser_semaphore.release()


def get_browser():
    """获取浏览器实例"""
    try:
        return BrowserPool.driver()
    except Exception as e:
        logger.error(f"线程 {threading.get_ident()} 获取浏览器实例失败: {str(e)}")
        raise


def release_browser():
    """释放浏览器资源"""
    BrowserPool.cleanup()