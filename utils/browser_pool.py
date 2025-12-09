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

# ========== 1. 新增：日志配置（替换print，便于排查并行问题） ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(thread)d - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== 2. 新增：并行限流核心配置（关键！） ==========
# 最大并发Chrome实例数（容器1核2G建议≤4，2核4G建议≤8，根据资源调整）
MAX_BROWSER_INSTANCES = 4
# 信号量：限制同时创建的Chrome实例数
browser_semaphore = threading.Semaphore(MAX_BROWSER_INSTANCES)
# 创建driver失败重试次数/间隔
RETRY_TIMES = 3
RETRY_DELAY = 2


class BrowserPool:
    _thread_local = local()  # 线程局部存储

    @classmethod
    def driver(cls):
        """获取当前线程的浏览器实例（线程安全+限流+重试）"""
        if not hasattr(cls._thread_local, 'driver'):
            # 3. 新增：限流（超出最大实例数则阻塞，避免资源耗尽）
            with browser_semaphore:
                cls._thread_local.driver = cls._create_driver_with_retry()
        return cls._thread_local.driver

    @classmethod
    def _create_driver_with_retry(cls):
        """新增：带重试的driver创建（解决临时资源竞争超时）"""
        for retry in range(RETRY_TIMES):
            try:
                return cls._create_driver()
            except (WebDriverException, TimeoutException, urllib3.exceptions.ReadTimeoutError) as e:
                logger.error(f"线程 {threading.get_ident()} 第{retry+1}次创建浏览器失败: {str(e)}")
                if retry == RETRY_TIMES - 1:  # 最后一次重试失败，抛异常
                    raise
                time.sleep(RETRY_DELAY)  # 重试前等待，缓解资源竞争
        raise Exception(f"线程 {threading.get_ident()} 超出{RETRY_TIMES}次重试，创建浏览器失败")

    @classmethod
    def _create_driver(cls):
        """优化后的浏览器创建方法（保留原有容器适配，新增超时/轻量化配置）"""
        logger.info(f"线程 {threading.get_ident()} 开始创建浏览器实例")

        chrome_options = Options()

        # ========== 原有核心配置保留 ==========
        chrome_options.add_argument("--headless=new")  # 无头模式（必加）
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")  # root用户运行必需
        chrome_options.add_argument("--disable-dev-shm-usage")  # 解决容器内存不足
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        # ======================================

        # ========== 4. 新增：轻量化+超时优化（关键解决并行超时） ==========
        # 禁用图片加载，减少资源占用
        chrome_options.add_argument("--disable-images")
        # 页面加载策略：DOM加载完成即可，无需等所有资源（减少超时概率）
        chrome_options.page_load_strategy = 'eager'
        # 禁用无用的渲染特性，降低CPU占用
        chrome_options.add_argument("--disable-features=NetworkService,NetworkServiceInProcess")
        # ======================================

        # ========== 临时目录优化（原有逻辑保留，加固异常处理） ==========
        temp_profile = None
        try:
            temp_profile = tempfile.mkdtemp(prefix="chrome_profile_", dir="/tmp")
            chrome_options.add_argument(f"--user-data-dir={temp_profile}")
            chrome_options.add_argument(f"--profile-directory=Profile{threading.get_ident()}")
        except Exception as e:
            logger.error(f"线程 {threading.get_ident()} 创建临时目录失败: {str(e)}")
            if temp_profile and os.path.exists(temp_profile):
                shutil.rmtree(temp_profile, ignore_errors=True)
            raise
        # ======================================

        # ========== ChromeDriver服务配置（新增超时+日志） ==========
        try:
            service = Service(
                executable_path="/usr/local/bin/chromedriver",
                log_path="/tmp/chromedriver_{}.log".format(threading.get_ident()),  # 按线程分日志，便于排查
                service_args=['--verbose', '--log-level=DEBUG']  # 输出详细日志，定位超时原因
            )
        except Exception as e:
            logger.warning(f"线程 {threading.get_ident()} 使用默认chromedriver路径: {str(e)}")
            service = Service()
        # ======================================

        # 创建driver（新增超时配置）
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            # 5. 新增：全局超时配置（适配并行场景）
            driver.set_page_load_timeout(60)  # 页面加载超时（默认30→60）
            driver.set_script_timeout(60)     # 脚本执行超时（屏蔽webdriver用）
            driver.implicitly_wait(15)        # 元素隐式等待（保留原有）

            # 屏蔽webdriver特征（新增重试，避免单次执行超时）
            for retry in range(2):
                try:
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    break
                except TimeoutException as e:
                    logger.warning(f"线程 {threading.get_ident()} 第{retry+1}次屏蔽webdriver失败: {str(e)}")
                    time.sleep(1)

            logger.info(f"线程 {threading.get_ident()} 浏览器实例创建成功（容器无头模式）")
            return driver
        except (WebDriverException, TimeoutException) as e:
            # 失败时清理临时目录
            if temp_profile and os.path.exists(temp_profile):
                shutil.rmtree(temp_profile, ignore_errors=True)
            logger.error(f"线程 {threading.get_ident()} 创建浏览器失败: {str(e)}")
            raise
        except Exception as e:
            if temp_profile and os.path.exists(temp_profile):
                shutil.rmtree(temp_profile, ignore_errors=True)
            logger.error(f"线程 {threading.get_ident()} 创建浏览器失败: {str(e)}")
            raise

    @classmethod
    def cleanup(cls):
        """清理当前线程的浏览器资源（加固释放+信号量）"""
        if hasattr(cls._thread_local, 'driver'):
            driver = cls._thread_local.driver
            try:
                logger.info(f"线程 {threading.get_ident()} 开始释放浏览器实例")
                driver.quit()  # 强制退出，避免容器残留进程
                logger.info(f"线程 {threading.get_ident()} 浏览器实例释放成功")
            except Exception as e:
                logger.error(f"线程 {threading.get_ident()} 释放浏览器异常: {str(e)}")
            finally:
                # 清理临时用户数据目录
                try:
                    if hasattr(driver, 'options'):
                        profile_path = None
                        for arg in driver.options.arguments:
                            if '--user-data-dir=' in arg:
                                profile_path = arg.split('=')[1]
                                break
                        if profile_path and os.path.exists(profile_path):
                            shutil.rmtree(profile_path, ignore_errors=True)
                            logger.info(f"线程 {threading.get_ident()} 清理临时目录: {profile_path}")
                except Exception as e:
                    logger.error(f"线程 {threading.get_ident()} 清理临时目录异常: {str(e)}")

                # 6. 新增：删除线程局部存储+释放信号量（关键！避免资源泄漏）
                del cls._thread_local.driver
                browser_semaphore.release()  # 释放信号量，允许其他线程创建实例


def get_browser():
    """获取当前线程的浏览器实例（对外接口，保持兼容）"""
    try:
        return BrowserPool.driver()
    except Exception as e:
        logger.error(f"线程 {threading.get_ident()} 获取浏览器实例失败: {str(e)}")
        raise


def release_browser():
    """释放当前线程的浏览器资源（对外接口，保持兼容）"""
    BrowserPool.cleanup()