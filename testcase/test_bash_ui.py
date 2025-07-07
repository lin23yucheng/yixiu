import time
import threading
import allure
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bash.push.client_bash import push_images_auto
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

    @staticmethod
    def run_push_client():
        """运行推图客户端"""
        try:
            push_images_auto()  # 调用非测试函数
        except Exception as e:
            allure.attach(f"推图失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)

    @allure.story("坐席分拣流程")
    def test_seat_operation(self):
        with allure.step("步骤1：林禹成账号登录bash系统"):
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

        with allure.step("步骤2：申请坐席"):
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

        with allure.step("步骤3：启动推图客户端"):
            # 创建并启动推图线程
            self.push_thread = threading.Thread(target=self.run_push_client)
            self.push_thread.daemon = True  # 设置为守护线程
            self.push_thread.start()
            allure.attach("推图客户端已启动", name="推图启动", attachment_type=allure.attachment_type.TEXT)

            # 添加等待，确保推图线程初始化完成
            time.sleep(2)  # 等待2秒让推图线程初始化
            allure.attach("推图线程初始化完成", name="推图状态", attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤4：等待图片出现并分拣"):
            # 循环直到产品名称为空
            while True:
                try:
                    # 等待产品名称元素出现
                    product_name = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//span[@class="product-name"]'))
                    )

                    # 当产品名称为JHOCT001时执行点击操作
                    if product_name.text == "JHOCT001":
                        # 获取canvas元素 - 修正索引方式
                        canvas_list = self.driver.find_elements(By.XPATH, '//canvas[@class="upper-canvas "]')
                        if not canvas_list:
                            raise Exception("未找到canvas元素")

                        # 点击前等待1秒并截图
                        time.sleep(1)
                        # 添加点击前截图到报告
                        allure.attach(
                            self.driver.get_screenshot_as_png(),
                            name=f"点击前截图-{time.strftime('%H%M%S')}",
                            attachment_type=allure.attachment_type.PNG
                        )

                        # 使用ActionChains在左上角(10,10)位置点击
                        action = ActionChains(self.driver)
                        action.move_to_element_with_offset(canvas_list[0], 10, 10).click().perform()
                        allure.attach(f"在canvas元素上点击 (10,10)", name="点击操作",
                                      attachment_type=allure.attachment_type.TEXT)

                        # 点击后等待1秒
                        time.sleep(1)
                        # 添加点击后截图到报告
                        allure.attach(
                            self.driver.get_screenshot_as_png(),
                            name=f"点击后截图-{time.strftime('%H%M%S')}",
                            attachment_type=allure.attachment_type.PNG
                        )

                        # 继续下一次循环
                        continue

                    # 当产品名称为空时执行离席操作
                    elif product_name.text.strip() == "":
                        # 点击申请离席
                        leave_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"申请离席")]'))
                        )
                        leave_button.click()
                        allure.attach("点击申请离席按钮", name="离席操作", attachment_type=allure.attachment_type.TEXT)

                        # 验证离席提示
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, '//p[@class="el-message__content" and contains(text(), "您已离席！")]'))
                            )
                            allure.attach("检测到消息: 您已离席！", name="离席状态",
                                          attachment_type=allure.attachment_type.TEXT)
                        except Exception as e:
                            allure.attach(f"未检测到离席提示: {str(e)}", name="警告",
                                          attachment_type=allure.attachment_type.TEXT)

                        # 结束循环
                        break

                except Exception as e:
                    allure.attach(f"操作异常: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                    # 添加异常截图
                    allure.attach(
                        self.driver.get_screenshot_as_png(),
                        name=f"异常截图-{time.strftime('%H%M%S')}",
                        attachment_type=allure.attachment_type.PNG
                    )
                    # 添加页面HTML
                    allure.attach(
                        self.driver.page_source,
                        name="异常时页面HTML",
                        attachment_type=allure.attachment_type.HTML
                    )
                    raise

    @classmethod
    def teardown_class(cls):
        cls.driver.quit()
