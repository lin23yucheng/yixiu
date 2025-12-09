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

# ========== 核心修改：固定本地ChromeDriver路径（与bash脚本对齐） ==========
LOCAL_CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"


def setup_chromedriver():
    """强制使用本地ChromeDriver（禁用自动下载）"""
    try:
        # 验证本地ChromeDriver是否存在且可执行
        if not os.path.exists(LOCAL_CHROMEDRIVER_PATH):
            raise FileNotFoundError(f"ChromeDriver文件不存在: {LOCAL_CHROMEDRIVER_PATH}")
        if not os.access(LOCAL_CHROMEDRIVER_PATH, os.X_OK):
            raise PermissionError(f"ChromeDriver无执行权限: {LOCAL_CHROMEDRIVER_PATH}")

        logger.info(f"使用本地ChromeDriver: {LOCAL_CHROMEDRIVER_PATH}")
        # 验证Driver版本（可选，确保与Chrome匹配）
        try:
            result = subprocess.run(
                [LOCAL_CHROMEDRIVER_PATH, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                driver_version = result.stdout.strip()
                logger.info(f"ChromeDriver版本: {driver_version}")
        except Exception as e:
            logger.warning(f"验证ChromeDriver版本失败: {str(e)}")

        return Service(executable_path=LOCAL_CHROMEDRIVER_PATH)
    except Exception as e:
        logger.error(f"设置ChromeDriver失败: {str(e)}")
        raise


def find_chrome_binary():
    """查找系统上的Chrome或Chromium二进制文件路径"""
    # 优先读取环境变量（bash脚本中设置的CHROME_BIN_PATH）
    chrome_env_path = os.getenv("CHROME_BIN_PATH")
    if chrome_env_path and os.path.exists(chrome_env_path) and os.access(chrome_env_path, os.X_OK):
        logger.info(f"从环境变量找到Chrome二进制文件: {chrome_env_path}")
        return chrome_env_path

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

    logger.error("未找到Chrome或Chromium二进制文件")
    raise FileNotFoundError("Chrome浏览器未安装，请检查环境")


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

        # ========== Chrome增强配置（容器/内网适配） ==========
        # 无头模式（必选，Zadig容器无界面）
        chrome_options.add_argument("--headless=new")
        # 容器环境必需
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # 窗口大小
        chrome_options.add_argument("--window-size=1920,1080")
        # 禁用不必要组件
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-images")  # 禁用图片加载，加快速度
        # 屏蔽自动化检测
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # 页面加载策略（eager比normal快，减少超时）
        chrome_options.page_load_strategy = 'eager'
        # 忽略证书错误（内网测试必选）
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        # 禁用日志冗余输出
        chrome_options.add_argument("--log-level=3")
        # 禁用网络安全限制（内网测试可选）
        chrome_options.add_argument("--disable-web-security")

        # 设置Chrome二进制文件路径
        try:
            chrome_binary = find_chrome_binary()
            chrome_options.binary_location = chrome_binary
            logger.info(f"使用Chrome路径: {chrome_binary}")
        except FileNotFoundError as e:
            logger.error(f"线程 {threading.get_ident()} Chrome路径配置失败: {str(e)}")
            raise

        # ========== 强制使用本地ChromeDriver ==========
        try:
            service = setup_chromedriver()
            # 禁用Driver日志（减少干扰）
            service.log_output = os.devnull
        except Exception as e:
            logger.error(f"线程 {threading.get_ident()} 设置ChromeDriver服务失败: {str(e)}")
            raise

        # 创建driver
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 超时配置（优化避免TimeoutException）
            driver.set_page_load_timeout(30)  # 缩短超时时间，避免长时间等待
            driver.set_script_timeout(30)
            driver.implicitly_wait(10)  # 缩短隐式等待

            # 屏蔽webdriver特征
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            })

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
                # 修复：仅当信号量已获取时释放（避免重复释放）
                if browser_semaphore._value < MAX_BROWSER_INSTANCES:
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