import threading
import os
import tempfile
import shutil
import logging
import time
from threading import local
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
import urllib3
import subprocess

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


# ========== 新增：Chrome/ChromeDriver版本检查 ==========
def check_chrome_version():
    """检查Chrome和ChromeDriver版本是否匹配"""
    try:
        # 获取Chrome版本
        chrome_version = subprocess.check_output(
            ["google-chrome", "--version"],
            stderr=subprocess.STDOUT
        ).decode().strip()
        chrome_main_version = chrome_version.split()[2].split('.')[0]

        # 获取ChromeDriver版本
        chromedriver_version = subprocess.check_output(
            ["/usr/local/bin/chromedriver", "--version"],
            stderr=subprocess.STDOUT
        ).decode().strip()
        chromedriver_main_version = chromedriver_version.split()[1].split('.')[0]

        if chrome_main_version != chromedriver_main_version:
            logger.error(f"版本不匹配！Chrome: {chrome_main_version}, ChromeDriver: {chromedriver_main_version}")
            return False
        logger.info(f"版本匹配：Chrome {chrome_main_version} ↔ ChromeDriver {chromedriver_main_version}")
        return True
    except Exception as e:
        logger.error(f"检查Chrome版本失败: {str(e)}")
        return False


def fix_chromedriver_permission():
    """修复ChromeDriver可执行权限"""
    try:
        os.chmod("/usr/local/bin/chromedriver", 0o755)  # 赋予可执行权限
        logger.info("ChromeDriver权限已设置为755")
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
        # ======================================================

        # ========== 临时目录：使用系统默认，避免权限问题 ==========
        # 注释掉自定义temp_profile，改用Chrome默认临时目录（减少权限问题）
        # temp_profile = tempfile.mkdtemp(prefix="chrome_profile_", dir="/tmp")
        # chrome_options.add_argument(f"--user-data-dir={temp_profile}")
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
            # 失败时不清理temp_profile（已注释）
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