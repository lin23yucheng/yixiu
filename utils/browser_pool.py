import threading
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import local


class BrowserPool:
    _thread_local = local()  # 线程局部存储
    _drivers = {}  # 改为线程->驱动的映射

    @classmethod
    def get_driver(cls):
        thread_id = threading.get_ident()
        if thread_id not in cls._drivers:
            cls._drivers[thread_id] = webdriver.Chrome()
        return cls._drivers[thread_id]

    @classmethod
    def quit_all(cls):
        for driver in cls._drivers.values():
            driver.quit()
        cls._drivers.clear()

    @classmethod
    def driver(cls):
        """获取当前线程的浏览器实例（线程安全）"""
        if not hasattr(cls._thread_local, 'driver'):
            cls._thread_local.driver = cls._create_driver()
        return cls._thread_local.driver

    @classmethod
    def _create_driver(cls):
        """创建浏览器实例（含修复的chrome_options）"""
        chrome_options = Options()
        # 加速启动参数
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        # 用户数据目录
        profile_dir = os.path.join(os.path.expanduser("~"), ".selenium_chrome_profile")
        os.makedirs(profile_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # 禁用自动化特征
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        print(f"线程 {threading.get_ident()} 创建浏览器实例")
        return webdriver.Chrome(options=chrome_options)

    @classmethod
    def cleanup(cls):
        """清理当前线程的浏览器资源"""
        if hasattr(cls._thread_local, 'driver'):
            try:
                cls._thread_local.driver.quit()
                print(f"线程 {threading.get_ident()} 释放浏览器实例")
            except Exception as e:
                print(f"释放浏览器异常: {str(e)}")
            finally:
                del cls._thread_local.driver


# 全局访问点
def get_browser():
    """获取当前线程的浏览器实例"""
    return BrowserPool.driver()


def release_browser():
    """释放当前线程的浏览器资源"""
    BrowserPool.cleanup()
