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
MAX_BROWSER_INSTANCES = 2
browser_semaphore = threading.Semaphore(MAX_BROWSER_INSTANCES)
RETRY_TIMES = 2
RETRY_DELAY = 3


# ========== 新增：使用webdriver-manager自动管理ChromeDriver ==========
def setup_chromedriver():
    """使用webdriver-manager自动安装和管理ChromeDriver"""
    try:
        # 尝试导入webdriver_manager
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService

        logger.info("使用webdriver-manager自动管理ChromeDriver")

        # 自动下载并获取ChromeDriver路径
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver已安装到: {driver_path}")

        return ChromeService(executable_path=driver_path)
    except ImportError:
        logger.warning("webdriver-manager未安装，使用系统ChromeDriver")
        # 检查系统ChromeDriver
        chromedriver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]

        for path in chromedriver_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"使用系统ChromeDriver: {path}")
                return Service(executable_path=path)

        logger.error("未找到可用的ChromeDriver")
        raise Exception("未找到ChromeDriver，请安装webdriver-manager或手动安装ChromeDriver")
    except Exception as e:
        logger.error(f"设置ChromeDriver失败: {str(e)}")
        raise


def find_chrome_binary():
    """查找系统上的Chrome或Chromium二进制文件路径"""
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


class BrowserPool:
    _thread_local = local()

    @classmethod
    def driver(cls):
        """获取当前线程的浏览器实例"""
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
        """创建浏览器实例"""
        logger.info(f"线程 {threading.get_ident()} 开始创建浏览器实例")

        chrome_options = Options()

        # ========== Chrome配置 ==========
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.page_load_strategy = 'eager'

        # 设置Chrome二进制文件路径
        chrome_binary = find_chrome_binary()
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            logger.info(f"使用Chrome路径: {chrome_binary}")
        else:
            logger.warning("未找到Chrome二进制文件，使用默认路径")

        # ========== 使用webdriver-manager管理ChromeDriver ==========
        try:
            service = setup_chromedriver()
        except Exception as e:
            logger.error(f"设置ChromeDriver服务失败: {str(e)}")
            # 尝试使用默认Service
            service = Service()

        # 创建driver
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 超时配置
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)
            driver.implicitly_wait(15)

            # 屏蔽webdriver
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