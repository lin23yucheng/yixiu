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
RETRY_TIMES = 3  # 增加重试次数（从2→3）
RETRY_DELAY = 5  # 增加重试间隔（从3→5秒）

# ========== 核心配置：固定本地ChromeDriver路径 ==========
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
        # 验证Driver版本
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

        # 修复：使用subprocess.DEVNULL（正确的文件描述符）
        service = Service(executable_path=LOCAL_CHROMEDRIVER_PATH)
        service.log_output = subprocess.DEVNULL
        return service
    except Exception as e:
        logger.error(f"设置ChromeDriver失败: {str(e)}")
        raise


def find_chrome_binary():
    """查找系统上的Chrome二进制文件路径"""
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
        """带重试的driver创建（增加重试次数）"""
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
        """创建浏览器实例（核心优化：解决超时/渲染问题）"""
        logger.info(f"线程 {threading.get_ident()} 开始创建浏览器实例")

        chrome_options = Options()

        # ========== 核心优化：Chrome配置（解决超时/无头渲染问题） ==========
        # 1. 禁用网络相关的阻塞功能
        chrome_options.add_argument("--disable-features=NetworkService")  # 禁用网络服务，减少资源占用
        chrome_options.add_argument("--disable-features=NetworkServiceInProcess")

        # 2. 调整页面加载策略为"none"（完全不等待资源加载，仅加载DOM）
        chrome_options.page_load_strategy = 'none'  # 替代原来的'eager'，更激进的加载策略

        # 3. 禁用缓存（避免旧资源干扰）
        chrome_options.add_argument("--disable-cache")
        chrome_options.add_argument("--disable-application-cache")

        # 4. 强制使用HTTP/1.1（避免HTTP/2的兼容性问题）
        chrome_options.add_argument("--force-fieldtrials=*DisableHTTP2/Enabled/")

        # 1. 无头模式增强（避免检测+渲染异常）
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用自动化检测
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")  # 修复无头模式渲染

        # 2. 容器环境必需
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        # 3. 网络/加载优化（解决内网慢加载）
        chrome_options.add_argument("--disable-network-throttling")  # 禁用网络节流
        chrome_options.add_argument("--disable-background-networking")  # 禁用后台网络
        chrome_options.add_argument("--enable-javascript")  # 强制启用JS
        chrome_options.add_argument("--disable-images")  # 禁用图片加速加载
        chrome_options.add_argument("--window-size=1920,1080")  # 固定窗口大小

        # 4. 屏蔽自动化特征
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 5. 页面加载策略（eager比normal快，减少超时）
        chrome_options.page_load_strategy = 'eager'

        # 6. 忽略证书/SSL错误（内网必选）
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-insecure-localhost")  # 允许不安全的本地主机

        # 7. 禁用冗余日志
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")

        # 设置Chrome二进制文件路径
        try:
            chrome_binary = find_chrome_binary()
            chrome_options.binary_location = chrome_binary
            logger.info(f"使用Chrome路径: {chrome_binary}")
        except FileNotFoundError as e:
            logger.error(f"线程 {threading.get_ident()} Chrome路径配置失败: {str(e)}")
            raise

        # 强制使用本地ChromeDriver
        try:
            service = setup_chromedriver()
        except Exception as e:
            logger.error(f"线程 {threading.get_ident()} 设置ChromeDriver服务失败: {str(e)}")
            raise

        # 创建driver
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # ========== 超时配置优化（适配内网慢加载） ==========
            driver.set_page_load_timeout(60)  # 页面加载超时延长到60秒
            driver.set_script_timeout(60)  # 脚本执行超时延长到60秒
            driver.implicitly_wait(20)  # 隐式等待延长到20秒

            # 强化屏蔽webdriver特征
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # 模拟真实UA
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.40 Safari/537.36"
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
                # 修复：仅当信号量已获取时释放
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
