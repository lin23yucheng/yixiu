import time
import threading
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bash.push.client_bash import test_logic_auto


@allure.feature("场景：bash坐席分拣图片")
class TestBashUI:
    @classmethod
    def setup_class(cls):
        # 初始化浏览器
        cls.driver = webdriver.Chrome()
        cls.driver.maximize_window()
        # 登录信息
        cls.username = "19166459858"
        cls.password = "123456"
        # 推图线程控制
        cls.push_thread = None
        cls.push_completed = threading.Event()

    @allure.story("坐席分拣流程")
    def test_seat_operation(self):
        # 步骤1：登录
        with allure.step("林禹成账号登录bash系统"):
            self.driver.get("http://fat-bash-web.svfactory.com:6180/#/signIn")
            # 输入账号
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入账号"]'))
            )
            username_input.send_keys(self.username)
            # 输入密码
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入密码"]'))
            )
            password_input.send_keys(self.password)
            # 点击登录按钮
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='登录']"))
            )
            login_button.click()

        # 步骤2：申请坐席
        with allure.step("申请坐席"):
            # 等待进入首页
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]"))
            )

            # 验证初始坐席状态为"我已离席"
            status_text = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='status-text']"))
            )
            if status_text.text != "我已离席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误",
                              attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"初始坐席状态应为'我已离席'，实际为: {status_text.text}")
            allure.attach("初始坐席状态: 我已离席", name="状态验证", attachment_type=allure.attachment_type.TEXT)

            # 点击申请坐席按钮
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'申请坐席')]"))
            )
            apply_button.click()

            # 等待并验证连接消息
            try:
                # 等待"正在建立连接"消息
                connecting_msg = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '正在建立连接')]"))
                )
                allure.attach("检测到消息: 正在建立连接", name="连接状态", attachment_type=allure.attachment_type.TEXT)

                # 等待"连接建立成功"消息
                success_msg = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '连接建立成功')]"))
                )
                allure.attach("检测到消息: 连接建立成功", name="连接状态", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                allure.attach(f"连接消息验证失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                raise

            # 验证坐席状态变为"我已坐席"
            def check_seat_status():
                status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
                return status_text.text == "我已坐席"

            # 等待状态变化，最多10秒
            WebDriverWait(self.driver, 10).until(lambda driver: check_seat_status())
            status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
            allure.attach(f"当前坐席状态: {status_text.text}", name="状态验证",
                          attachment_type=allure.attachment_type.TEXT)

            if status_text.text != "我已坐席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误",
                              attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"申请坐席后状态应为'我已坐席'，实际为: {status_text.text}")

        # 步骤3：启动推图线程
        with allure.step("启动推图客户端"):
            # 创建并启动推图线程
            self.push_thread = threading.Thread(target=self.run_push_client)
            self.push_thread.daemon = True  # 设置为守护线程
            self.push_thread.start()
            allure.attach("推图客户端已启动", name="推图启动", attachment_type=allure.attachment_type.TEXT)

            # 添加等待，确保推图线程初始化完成
            time.sleep(3)  # 等待3秒让推图线程初始化
            allure.attach("推图线程初始化完成", name="推图状态", attachment_type=allure.attachment_type.TEXT)

        # 步骤4：等待图片出现并分拣
        with allure.step("分拣图片"):
            # 添加调试信息：打印当前页面HTML
            allure.attach(
                self.driver.page_source,
                name="当前页面HTML",
                attachment_type=allure.attachment_type.HTML
            )

            # 添加截图到报告
            allure.attach(
                self.driver.get_screenshot_as_png(),
                name="等待图片时的页面截图",
                attachment_type=allure.attachment_type.PNG
            )

            # 尝试多种定位方式
            try:
                # 方式1：使用类名定位
                image_div = WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='image-container']"))
                )
            except:
                try:
                    # 方式2：使用更通用的图片容器定位
                    image_div = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'image')]"))
                    )
                except:
                    # 方式3：使用图片标签定位
                    image_div = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.TAG_NAME, "img"))
                    )

            allure.attach("检测到图片", name="图片出现", attachment_type=allure.attachment_type.TEXT)

            # 添加图片出现时的截图
            allure.attach(
                self.driver.get_screenshot_as_png(),
                name="图片出现时的页面截图",
                attachment_type=allure.attachment_type.PNG
            )

            # 第一次点击（分拣NG）
            image_div.click()
            allure.attach("第一次点击（分拣NG）", name="分拣操作", attachment_type=allure.attachment_type.TEXT)
            time.sleep(5)  # 间隔5秒

            # 第二次点击
            image_div.click()
            allure.attach("第二次点击（分拣NG）", name="分拣操作", attachment_type=allure.attachment_type.TEXT)

            # 确认分拣完成
            confirm_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'完成分拣')]"))
            )
            confirm_button.click()
            allure.attach("分拣完成", name="分拣结果", attachment_type=allure.attachment_type.TEXT)

        # 步骤5：等待推图完成
        with allure.step("等待推图完成"):
            # 等待推图线程结束或超时
            self.push_thread.join(timeout=120)  # 最多等待2分钟
            if self.push_thread.is_alive():
                allure.attach("推图超时", name="警告", attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach("推图完成", name="推图状态", attachment_type=allure.attachment_type.TEXT)

    def run_push_client(self):
        """运行推图客户端"""
        try:
            test_logic_auto()
            self.push_completed.set()
        except Exception as e:
            allure.attach(f"推图失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)

    @classmethod
    def teardown_class(cls):
        # 关闭浏览器
        cls.driver.quit()
