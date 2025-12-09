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
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from utils.browser_pool import get_browser, release_browser

# ========== 1. 新增/优化全局超时配置（核心：避免无限等待） ==========
# 基础元素定位超时（容器并行建议20-30秒）
BASE_TIMEOUT = 25
# 关键操作超时（如连接建立、状态切换）
CRITICAL_TIMEOUT = 40
# 推图监控最大空等待次数（适配容器推图延迟）
MAX_EMPTY_COUNT = 25
# 推图监控检查间隔（秒）
CHECK_INTERVAL = 2
# 元素定位重试次数
ELEMENT_RETRY = 3
# 分拣循环总超时（秒）：防止无限循环导致TimeoutException
SORT_TOTAL_TIMEOUT = 300  # 5分钟
# 推图线程等待超时（秒）
PUSH_THREAD_TIMEOUT = 60


# ==============================================================

@allure.feature("场景：bash坐席分拣流程")
class TestBashUI:
    @classmethod
    def setup_class(cls):
        # ========== 浏览器池获取实例（保留核心逻辑） ==========
        cls.driver = get_browser()
        cls.driver.set_page_load_timeout(CRITICAL_TIMEOUT)  # 页面加载超时
        cls.driver.set_script_timeout(CRITICAL_TIMEOUT)  # 新增：脚本执行超时
        # ======================================================

        # 读取配置文件（路径兼容Linux+指定编码，加固异常处理）
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'env_config.ini')
            config_path = os.path.abspath(config_path)
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')

            # 获取账号密码（增加配置项检查）
            cls.username = config.get('bash', 'myself_account', fallback='')
            cls.password = config.get('bash', 'myself_password', fallback='')
            cls.miaiproductcode = config.get('Inspection', 'miai-product-code', fallback='')

            # 校验配置非空
            if not all([cls.username, cls.password, cls.miaiproductcode]):
                raise ValueError("配置文件中账号/密码/产品编码为空！")
        except Exception as e:
            allure.attach(f"读取配置失败: {str(e)}", name="配置错误", attachment_type=allure.attachment_type.TEXT)
            raise

        # ========== 2. 推图线程控制加固（避免线程泄漏） ==========
        cls.push_thread = None
        cls.push_completed = threading.Event()  # 标记推图完成
        cls.push_lock = threading.Lock()  # 线程安全锁
        # 新增：分拣循环开始时间（用于总超时控制）
        cls.sort_start_time = None
        # ======================================================

    @classmethod
    def _retry_find_element(cls, locator, timeout=BASE_TIMEOUT, wait_clickable=False):
        """优化：元素定位重试（增加可交互等待+日志+截图）"""
        locator_name = f"{locator[0]}={locator[1]}"
        for retry in range(ELEMENT_RETRY + 1):
            try:
                allure.attach(f"第{retry + 1}次定位元素: {locator_name}", name="元素定位",
                              attachment_type=allure.attachment_type.TEXT)
                if wait_clickable:
                    # 优先等待可点击（更精准，避免元素存在但不可用）
                    element = WebDriverWait(cls.driver, timeout).until(
                        EC.element_to_be_clickable(locator)
                    )
                else:
                    # 等待元素存在
                    element = WebDriverWait(cls.driver, timeout).until(
                        EC.presence_of_element_located(locator)
                    )
                allure.attach(f"元素定位成功: {locator_name}", name="元素定位",
                              attachment_type=allure.attachment_type.TEXT)
                return element
            except (TimeoutException, StaleElementReferenceException) as e:
                if retry == ELEMENT_RETRY:
                    # 最后一次失败：保存截图+源码
                    allure.attach(cls.driver.get_screenshot_as_png(), name=f"定位失败截图-{locator_name}",
                                  attachment_type=allure.attachment_type.PNG)
                    allure.attach(cls.driver.page_source, name=f"定位失败源码-{locator_name}",
                                  attachment_type=allure.attachment_type.HTML)
                    raise TimeoutException(f"元素定位失败（重试{ELEMENT_RETRY}次）: {locator_name}, 错误: {str(e)}")
                # 重试前刷新页面+等待
                cls.driver.refresh()
                time.sleep(2)
                allure.attach(f"元素定位失败，刷新页面重试: {locator_name}", name="元素定位重试",
                              attachment_type=allure.attachment_type.TEXT)
        raise TimeoutException(f"元素定位失败: {locator_name}")

    @staticmethod
    def run_push_client(push_completed, product_code):
        """优化：传入产品编码，增加推图日志"""
        try:
            allure.attach(f"开始推图，产品编码: {product_code}", name="推图启动",
                          attachment_type=allure.attachment_type.TEXT)
            push_images_auto()  # 调用非测试函数
            push_completed.set()  # 推图成功，标记完成
            allure.attach("推图客户端执行完成", name="推图结果", attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            allure.attach(f"推图失败: {str(e)}", name="推图错误", attachment_type=allure.attachment_type.TEXT)
            push_completed.set()  # 即使失败，也标记完成，避免死等
            raise

    def _wait_push_complete(self):
        """新增：等待推图完成（带超时）"""
        allure.attach(f"等待推图完成，超时{self.PUSH_THREAD_TIMEOUT}秒", name="推图等待",
                      attachment_type=allure.attachment_type.TEXT)
        # 等待Event触发或超时
        push_success = self.push_completed.wait(timeout=self.PUSH_THREAD_TIMEOUT)
        if not push_success:
            allure.attach("推图线程超时未完成", name="推图超时", attachment_type=allure.attachment_type.TEXT)
            raise TimeoutException(f"推图线程等待超时（{self.PUSH_THREAD_TIMEOUT}秒）")
        # 验证推图线程是否存活
        if self.push_thread and self.push_thread.is_alive():
            allure.attach("推图线程仍在运行，强制等待结束", name="推图线程状态",
                          attachment_type=allure.attachment_type.TEXT)
            self.push_thread.join(timeout=10)

    def _verify_seat_status(self, expected_status, timeout=CRITICAL_TIMEOUT):
        """新增：通用坐席状态验证"""

        def check_status():
            try:
                status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']").text.strip()
                return status_text == expected_status
            except NoSuchElementException:
                return False

        allure.attach(f"等待坐席状态变为: {expected_status}", name="状态验证",
                      attachment_type=allure.attachment_type.TEXT)
        status_ok = WebDriverWait(self.driver, timeout).until(check_status)
        if not status_ok:
            current_status = self.driver.find_element(By.XPATH, "//span[@class='status-text']").text.strip()
            allure.attach(f"状态验证失败，预期: {expected_status}, 实际: {current_status}", name="状态错误",
                          attachment_type=allure.attachment_type.TEXT)
            raise AssertionError(f"坐席状态验证失败，预期: {expected_status}, 实际: {current_status}")
        allure.attach(f"坐席状态验证成功: {expected_status}", name="状态验证",
                      attachment_type=allure.attachment_type.TEXT)

    @allure.story("启动推图&分拣图片")
    def test_seat_operation(self):
        # 初始化分拣循环总超时
        self.sort_start_time = time.time()

        with allure.step("步骤1：林禹成账号登录bash系统"):
            # 兼容Linux容器网络，增加页面加载失败重试
            login_url = "http://fat-bash-web.svfactory.com:6180/#/signIn"
            for retry in range(3):  # 重试次数从2→3
                try:
                    self.driver.get(login_url)
                    allure.attach(f"访问登录页: {login_url}", name="页面访问",
                                  attachment_type=allure.attachment_type.TEXT)
                    # 优化：不仅等title，还等账号输入框（更精准）
                    WebDriverWait(self.driver, CRITICAL_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入账号"]'))
                    )
                    # 验证页面标题
                    WebDriverWait(self.driver, 10).until(EC.title_contains("登录"))
                    allure.attach("登录页加载成功", name="页面加载", attachment_type=allure.attachment_type.TEXT)
                    break
                except TimeoutException as e:
                    if retry == 2:
                        allure.attach(f"页面加载超时: {str(e)}", name="页面加载错误",
                                      attachment_type=allure.attachment_type.TEXT)
                        allure.attach(self.driver.get_screenshot_as_png(), name="登录页加载失败截图",
                                      attachment_type=allure.attachment_type.PNG)
                        allure.attach(self.driver.page_source, name="登录页加载失败源码",
                                      attachment_type=allure.attachment_type.HTML)
                        raise
                    allure.attach(f"登录页加载失败，第{retry + 1}次重试", name="页面重试",
                                  attachment_type=allure.attachment_type.TEXT)
                    self.driver.refresh()
                    time.sleep(3)  # 延长重试间隔

            # 输入账号（使用重试函数，等待可交互）
            username_input = self._retry_find_element((By.XPATH, '//input[@placeholder="请输入账号"]'),
                                                      wait_clickable=True)
            username_input.clear()
            username_input.send_keys(self.username)
            allure.attach(f"输入账号: {self.username}", name="登录操作", attachment_type=allure.attachment_type.TEXT)

            # 输入密码（使用重试函数，等待可交互）
            password_input = self._retry_find_element((By.XPATH, '//input[@placeholder="请输入密码"]'),
                                                      wait_clickable=True)
            password_input.clear()
            password_input.send_keys(self.password)
            allure.attach("输入密码: ***", name="登录操作", attachment_type=allure.attachment_type.TEXT)

            # 点击登录按钮（等待可点击+重试）
            login_button = self._retry_find_element((By.XPATH, "//span[text()='登录']"), wait_clickable=True)
            login_button.click()
            allure.attach("点击登录按钮", name="登录操作", attachment_type=allure.attachment_type.TEXT)
            time.sleep(4)  # 登录后等待页面跳转（延长至4秒）

        with allure.step("步骤2：申请坐席"):
            # 等待进入首页（使用重试函数，等待可交互）
            self._retry_find_element((By.XPATH, "//div[contains(@class, 'dashboard')]"), CRITICAL_TIMEOUT)
            allure.attach("进入首页成功", name="首页加载", attachment_type=allure.attachment_type.TEXT)

            # 验证初始坐席状态为"我已离席"
            self._verify_seat_status("我已离席")

            # 点击申请坐席按钮（等待可点击）
            apply_button = self._retry_find_element((By.XPATH, "//span[contains(text(),'申请坐席')]"),
                                                    wait_clickable=True)
            apply_button.click()
            allure.attach("点击申请坐席按钮", name="坐席操作", attachment_type=allure.attachment_type.TEXT)

            # 等待并验证连接消息（加固超时逻辑）
            try:
                # 等待"正在建立连接"消息
                connecting_msg = WebDriverWait(self.driver, CRITICAL_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '正在建立连接')]"))
                )
                allure.attach("检测到消息: 正在建立连接", name="连接状态", attachment_type=allure.attachment_type.TEXT)

                # 等待"连接建立成功"消息
                success_msg = WebDriverWait(self.driver, CRITICAL_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//p[@class='el-message__content' and contains(text(), '连接建立成功')]"))
                )
                allure.attach("检测到消息: 连接建立成功", name="连接状态", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                allure.attach(self.driver.get_screenshot_as_png(), name="连接失败截图",
                              attachment_type=allure.attachment_type.PNG)
                allure.attach(self.driver.page_source, name="连接失败页面源码",
                              attachment_type=allure.attachment_type.HTML)
                allure.attach(f"连接消息验证失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                # 异常时强制离席
                self._leave_seat()
                raise

            # 验证坐席状态变为"我已坐席"
            self._verify_seat_status("我已坐席")

        with allure.step("步骤3：启动推图客户端"):
            # ========== 推图线程加固（线程安全+超时控制） ==========
            with self.push_lock:
                if self.push_thread is None or not self.push_thread.is_alive():
                    # 重置推图完成标记
                    self.push_completed.clear()
                    # 启动推图线程，传入完成标记+产品编码
                    self.push_thread = threading.Thread(
                        target=self.run_push_client,
                        args=(self.push_completed, self.miaiproductcode)
                    )
                    self.push_thread.daemon = True
                    self.push_thread.start()
                    allure.attach("推图客户端已启动", name="推图启动", attachment_type=allure.attachment_type.TEXT)

                    # 等待推图线程初始化+推图完成
                    time.sleep(10)  # 延长至10秒，适配容器性能
                    # 等待推图完成（带超时）
                    self._wait_push_complete()
            # ======================================================

        with allure.step("步骤4：等待图片出现并分拣"):
            empty_counter = 0
            allure.attach(f"开始分拣监控，总超时{SORT_TOTAL_TIMEOUT}秒", name="分拣启动",
                          attachment_type=allure.attachment_type.TEXT)

            while True:
                # 检查分拣总超时
                elapsed_time = time.time() - self.sort_start_time
                if elapsed_time > SORT_TOTAL_TIMEOUT:
                    allure.attach(f"分拣循环总超时（{elapsed_time:.1f}秒 > {SORT_TOTAL_TIMEOUT}秒）", name="分拣超时",
                                  attachment_type=allure.attachment_type.TEXT)
                    self._leave_seat()
                    raise TimeoutException(f"分拣循环总超时（{SORT_TOTAL_TIMEOUT}秒）")

                try:
                    # 显式等待产品名称元素出现（使用重试函数）
                    product_name = self._retry_find_element((By.XPATH, '//span[@class="product-name"]'), BASE_TIMEOUT)
                    current_text = product_name.text.strip()
                    allure.attach(f"检测到产品名称: {current_text}", name="分拣状态",
                                  attachment_type=allure.attachment_type.TEXT)

                    # 情况1：检测到配置的产品名称
                    if current_text == self.miaiproductcode:
                        time.sleep(2)
                        empty_counter = 0

                        # 执行点击操作（加固元素存在性检查）
                        canvas_list = self.driver.find_elements(By.XPATH, '//canvas[@class="upper-canvas "]')
                        if canvas_list:
                            allure.attach(
                                self.driver.get_screenshot_as_png(),
                                name=f"点击前截图-{time.strftime('%H%M%S')}",
                                attachment_type=allure.attachment_type.PNG
                            )

                            # 优化点击逻辑（优先JS点击，确保生效）
                            try:
                                # 方案1：JS点击（最稳定）
                                self.driver.execute_script("arguments[0].click();", canvas_list[0])
                            except:
                                # 方案2：ActionChains双击
                                ActionChains(self.driver).move_to_element(canvas_list[0]).double_click().perform()
                            time.sleep(2)  # 延长点击后等待
                            allure.attach("图片分拣点击成功", name="分拣操作",
                                          attachment_type=allure.attachment_type.TEXT)

                        continue

                    # 情况2：检测到空文本
                    elif current_text == "":
                        empty_counter += 1
                        allure.attach(f"空产品名称，计数: {empty_counter}/{MAX_EMPTY_COUNT}", name="分拣状态",
                                      attachment_type=allure.attachment_type.TEXT)

                        # 检查推图是否完成，避免无意义等待
                        if self.push_completed.is_set():
                            allure.attach("推图已完成，无新图片，执行离席", name="推图状态",
                                          attachment_type=allure.attachment_type.TEXT)
                            self._leave_seat()
                            break

                        # 连续空次数达阈值，执行离席
                        if empty_counter >= MAX_EMPTY_COUNT:
                            allure.attach(f"连续{MAX_EMPTY_COUNT}次检测到空产品名称，执行离席", name="离席操作",
                                          attachment_type=allure.attachment_type.TEXT)
                            self._leave_seat()
                            break

                        time.sleep(CHECK_INTERVAL)
                        continue

                except Exception as e:
                    # 增强异常排查（记录当前空计数器+推图线程状态+已用时间）
                    allure.attach(f"空计数器: {empty_counter}", name="监控状态",
                                  attachment_type=allure.attachment_type.TEXT)
                    allure.attach(f"推图线程是否存活: {self.push_thread.is_alive() if self.push_thread else False}",
                                  name="线程状态", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(f"已用时间: {elapsed_time:.1f}秒", name="超时状态",
                                  attachment_type=allure.attachment_type.TEXT)
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
                    # 异常时强制离席，避免资源占用
                    self._leave_seat()
                    raise

    def _leave_seat(self):
        """新增：通用离席操作（加固逻辑）"""
        allure.attach("执行离席操作", name="离席启动", attachment_type=allure.attachment_type.TEXT)
        try:
            # 等待离席按钮可点击
            leave_button = WebDriverWait(self.driver, BASE_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"申请离席")]'))
            )
            leave_button.click()
            allure.attach("点击申请离席按钮", name="离席操作", attachment_type=allure.attachment_type.TEXT)
            time.sleep(10)  # 延长离席等待至10秒

            # 验证离席状态
            self._verify_seat_status("我已离席")
            allure.attach("离席成功，状态验证通过", name="离席结果", attachment_type=allure.attachment_type.TEXT)
        except Exception as e:
            allure.attach(f"离席操作失败: {str(e)}", name="离席错误", attachment_type=allure.attachment_type.TEXT)
            allure.attach(self.driver.get_screenshot_as_png(), name="离席失败截图",
                          attachment_type=allure.attachment_type.PNG)
            # 强制通过JS执行离席
            try:
                leave_button = self.driver.find_element(By.XPATH, '//span[contains(text(),"申请离席")]')
                self.driver.execute_script("arguments[0].click();", leave_button)
                allure.attach("通过JS强制离席成功", name="离席兜底", attachment_type=allure.attachment_type.TEXT)
            except:
                pass

    @classmethod
    def teardown_class(cls):
        # ========== 3. 推图线程兜底（确保线程终止） ==========
        if cls.push_thread and cls.push_thread.is_alive():
            try:
                # 等待推图线程结束，超时10秒强制退出
                cls.push_thread.join(timeout=10)
                allure.attach("推图线程已正常终止", name="线程清理", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                allure.attach(f"推图线程终止超时: {str(e)}", name="线程清理警告",
                              attachment_type=allure.attachment_type.TEXT)
        # ======================================================

        # ========== 浏览器资源清理加固（适配浏览器池） ==========
        if hasattr(cls, 'driver') and cls.driver:
            try:
                # 优先执行离席（兜底）
                if hasattr(cls, '_leave_seat'):
                    cls()._leave_seat()
                # 导航到空白页，释放页面资源
                cls.driver.get("about:blank")
                # 清除所有缓存/存储
                cls.driver.delete_all_cookies()
                cls.driver.execute_script("""
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                    try { indexedDB.databases().then(dbs => dbs.forEach(db => indexedDB.deleteDatabase(db.name))); } catch(e) {}
                """)
                time.sleep(2)  # 延长清理等待
                allure.attach("浏览器状态清理完成", name="资源清理", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                allure.attach(f"清理浏览器状态警告: {str(e)}", name="浏览器清理警告",
                              attachment_type=allure.attachment_type.TEXT)
        # ======================================================

        # 调用浏览器池的释放方法（核心！释放信号量）
        release_browser()
        allure.attach("浏览器资源已释放", name="资源清理", attachment_type=allure.attachment_type.TEXT)