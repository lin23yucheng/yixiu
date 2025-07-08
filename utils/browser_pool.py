import threading
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BrowserPool:
    _instance = None
    _lock = threading.Lock()
    _driver = None
    _ref_count = 0  # 引用计数器

    @classmethod
    def get_driver(cls):
        with cls._lock:
            if cls._driver is None:
                cls._init_driver()
            cls._ref_count += 1
            return cls._driver

    @classmethod
    def release_driver(cls):
        with cls._lock:
            cls._ref_count -= 1
            if cls._ref_count <= 0 and cls._driver is not None:
                cls._driver.quit()
                cls._driver = None

    @classmethod
    def _init_driver(cls):
        chrome_options = Options()

        # 加速启动参数
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        # 使用固定用户数据目录
        profile_dir = os.path.join(os.path.expanduser("~"), ".selenium_chrome_profile")
        os.makedirs(profile_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # 禁用不需要的功能
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 初始化浏览器
        cls._driver = webdriver.Chrome(options=chrome_options)
        print("浏览器实例已初始化并缓存")


# 单例访问点
def get_browser():
    return BrowserPool.get_driver()


def release_browser():
    BrowserPool.release_driver()
