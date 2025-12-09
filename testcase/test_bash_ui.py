import os
import time
import allure
import threading
import configparser
from time import sleep
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bash.push.client_bash import push_images_auto
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 恢复浏览器池引用（适配修改后的browser_pool.py）
from utils.browser_pool import get_browser, release_browser


@allure.feature("场景：bash坐席分拣流程")
class TestBashUI:
    @classmethod
    def setup_class(cls):
        # ========== 恢复浏览器池获取实例（核心！不再手动初始化Chrome） ==========
        cls.driver = get_browser()
        # ======================================================================

        # 读取配置文件（路径兼容Linux+指定编码）
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'env_config.ini')
        config_path = os.path.abspath(config_path)  # 转为绝对路径，避免Linux路径问题
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')  # 指定编码，避免中文乱码

        # 获取账号密码
        cls.username = config.get('bash', 'myself_account')
        cls.password = config.get('bash', 'myself_password')
        cls.miaiproductcode = config.get('Inspection', 'miai-product-code')

        # 推图线程控制
        cls.push_thread = None
        cls.push_completed = threading.Event()

    @staticmethod
    def run_push_client():
        """运行推图客户端"""
        try:
            push_images_auto()  # 调用非测试函数
        except Exception as e:
            allure.attach(f"推图失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)

    @allure.story("启动推图&分拣图片")
    def test_seat_operation(self):
        with allure.step("步骤1：林禹成账号登录bash系统"):
            # 兼容Linux容器网络，确保地址可访问
            self.driver.get("http://fat-bash-web.svfactory.com:6180/#/signIn")

            # 输入账号（延长超时至20秒，适配容器网络延迟）
            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入账号"]'))
            )
            username_input.clear()  # 新增：清空输入框，避免残留内容
            username_input.send_keys(self.username)

            # 输入密码
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入密码"]'))
            )
            password_input.clear()
            password_input.send_keys(self.password)

            # 点击登录按钮
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='登录']"))
            )
            login_button.click()
            # 新增：登录后等待页面跳转，避免操作过快
            time.sleep(3)

        with allure.step("步骤2：申请坐席"):
            # 等待进入首页（延长超时至20秒）
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]"))
            )

            # 验证初始坐席状态为"我已离席"
            status_text = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='status-text']"))
            )
            if status_text.text != "我已离席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误",
                              attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"初始坐席状态应为'我已离席'，实际为: {status_text.text}")
            allure.attach("初始坐席状态: 我已离席", name="状态验证", attachment_type=allure.attachment_type.TEXT)

            # 点击申请坐席按钮
            apply_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'申请坐席')]"))
            )
            apply_button.click()

            # 等待并验证连接消息（优化超时逻辑）
            try:
                # 等待"正在建立连接"消息
                connecting_msg = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '正在建立连接')]"))
                )
                allure.attach("检测到消息: 正在建立连接", name="连接状态", attachment_type=allure.attachment_type.TEXT)

                # 等待"连接建立成功"消息（延长超时至15秒）
                success_msg = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '连接建立成功')]"))
                )
                allure.attach("检测到消息: 连接建立成功", name="连接状态", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                # 新增：异常时截图+页面源码，便于排查
                allure.attach(self.driver.get_screenshot_as_png(), name="连接失败截图",
                              attachment_type=allure.attachment_type.PNG)
                allure.attach(self.driver.page_source, name="连接失败页面源码",
                              attachment_type=allure.attachment_type.HTML)
                allure.attach(f"连接消息验证失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                raise

            # 验证坐席状态变为"我已坐席"（优化等待逻辑）
            def check_seat_status():
                try:
                    status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
                    return status_text.text == "我已坐席"
                except:
                    return False

            # 等待状态变化，最多20秒
            WebDriverWait(self.driver, 20).until(lambda driver: check_seat_status())
            status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
            allure.attach(f"当前坐席状态: {status_text.text}", name="状态验证",
                          attachment_type=allure.attachment_type.TEXT)

            if status_text.text != "我已坐席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误",
                              attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"申请坐席后状态应为'我已坐席'，实际为: {status_text.text}")

        with allure.step("步骤3：启动推图客户端"):
            # 创建并启动推图线程
            self.push_thread = threading.Thread(target=self.run_push_client)
            self.push_thread.daemon = True  # 设置为守护线程
            self.push_thread.start()
            allure.attach("推图客户端已启动", name="推图启动", attachment_type=allure.attachment_type.TEXT)

            # 延长等待时间，确保推图线程初始化完成（适配容器性能）
            time.sleep(5)
            allure.attach("推图线程初始化完成", name="推图状态", attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤4：等待图片出现并分拣"):
            empty_counter = 0  # 记录连续为空的次数
            MAX_EMPTY_COUNT = 15  # 延长监控时间，适配容器推图延迟
            CHECK_INTERVAL = 2  # 每次检查间隔2秒，降低资源占用

            while True:
                try:
                    # 显式等待产品名称元素出现（延长超时至15秒）
                    product_name = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//span[@class="product-name"]'))
                    )
                    current_text = product_name.text.strip()

                    # 情况1：检测到配置的产品名称
                    if current_text == self.miaiproductcode:
                        time.sleep(2)  # 延长等待，确保元素可点击
                        empty_counter = 0  # 重置空状态计数器

                        # 执行点击操作
                        canvas_list = self.driver.find_elements(By.XPATH, '//canvas[@class="upper-canvas "]')
                        if canvas_list:
                            # 点击前截图
                            allure.attach(
                                self.driver.get_screenshot_as_png(),
                                name=f"点击前截图-{time.strftime('%H%M%S')}",
                                attachment_type=allure.attachment_type.PNG
                            )

                            # 优化点击逻辑，确保点击生效
                            ActionChains(self.driver).move_to_element_with_offset(
                                canvas_list[0], 10, 10
                            ).click().perform()
                            time.sleep(1)  # 点击后等待，避免重复操作

                        continue

                    # 情况2：检测到空文本
                    elif current_text == "":
                        empty_counter += 1
                        # 连续检测到空
                        if empty_counter >= MAX_EMPTY_COUNT:
                            # 执行离席操作
                            leave_button = WebDriverWait(self.driver, 20).until(
                                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"申请离席")]'))
                            )
                            leave_button.click()
                            sleep(5)  # 延长离席等待时间
                            allure.attach(f"连续{MAX_EMPTY_COUNT}秒检测到空产品名称，执行离席",
                                          name="离席操作",
                                          attachment_type=allure.attachment_type.TEXT)
                            break

                        # 未达阈值时短暂等待后继续监控
                        time.sleep(CHECK_INTERVAL)
                        continue

                except Exception as e:
                    # 增强异常排查信息
                    allure.attach(f"操作异常: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(
                        self.driver.get_screenshot_as_png(),
                        name=f"异常截图-{time.strftime('%H%M%S')}",
                        attachment_type=allure.attachment_type.PNG
                    )
                    allure.attach(
                        self.driver.page_source,
                        name="异常时页面HTML",
                        attachment_type=allure.attachment_type.HTML
                    )
                    raise

    @classmethod
    def teardown_class(cls):
        # 优化浏览器清理逻辑，复用browser_pool的release_browser
        if hasattr(cls, 'driver') and cls.driver:
            try:
                # 清除cookies和本地存储
                cls.driver.delete_all_cookies()
                cls.driver.execute_script("window.localStorage.clear();")
                cls.driver.execute_script("window.sessionStorage.clear();")

                # 导航到空白页释放资源
                cls.driver.get("about:blank")
            except Exception as e:
                print(f"清理浏览器状态时警告: {e}")
                allure.attach(f"清理警告: {str(e)}",
                              name="浏览器清理警告",
                              attachment_type=allure.attachment_type.TEXT)
        # 调用浏览器池的释放方法
        release_browser()