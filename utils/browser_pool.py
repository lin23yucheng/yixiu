import threading
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import local


class BrowserPool:
    _thread_local = local()  # 线程局部存储

    @classmethod
    def driver(cls):
        """获取当前线程的浏览器实例（线程安全）"""
        if not hasattr(cls._thread_local, 'driver'):
            cls._thread_local.driver = cls._create_driver()
        return cls._thread_local.driver

    @classmethod
    def _create_driver(cls):
        """优化后的浏览器创建方法"""
        # 添加加速参数
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-logging")  # 禁用日志减少输出
        chrome_options.add_argument("--log-level=3")  # 日志级别设置为警告及以上

        # 禁用不必要的功能
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 设置用户数据目录（复用用户数据）
        profile_dir = os.path.join(os.path.expanduser("~"), ".selenium_chrome_profile")
        os.makedirs(profile_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # 添加其他优化参数
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")

        # 创建并返回浏览器实例
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


def get_browser():
    """获取当前线程的浏览器实例"""
    return BrowserPool.driver()


def release_browser():
    """释放当前线程的浏览器资源"""
    BrowserPool.cleanup()
