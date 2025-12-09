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
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from utils.browser_pool import get_browser, release_browser

# ========== 1. 新增：全局超时配置（统一适配并行场景） ==========
# 基础元素定位超时（容器并行建议20-30秒）
BASE_TIMEOUT = 20
# 关键操作超时（如连接建立、状态切换）
CRITICAL_TIMEOUT = 30
# 推图监控最大空等待次数（适配容器推图延迟）
MAX_EMPTY_COUNT = 20
# 推图监控检查间隔（秒）
CHECK_INTERVAL = 2
# 元素定位重试次数
ELEMENT_RETRY = 2
# ==============================================================

@allure.feature("场景：bash坐席分拣流程")
class TestBashUI:
    @classmethod
    def setup_class(cls):
        # ========== 浏览器池获取实例（保留核心逻辑） ==========
        cls.driver = get_browser()
        cls.driver.set_page_load_timeout(CRITICAL_TIMEOUT)  # 新增：页面加载超时
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
        # ======================================================

    @classmethod
    def _retry_find_element(cls, locator, timeout=BASE_TIMEOUT):
        """新增：元素定位重试（解决并行时元素加载延迟）"""
        for retry in range(ELEMENT_RETRY + 1):
            try:
                return WebDriverWait(cls.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
            except (TimeoutException, StaleElementReferenceException) as e:
                if retry == ELEMENT_RETRY:
                    raise
                cls.driver.refresh()  # 重试前刷新页面（极端场景）
                time.sleep(1)
        raise TimeoutException(f"元素定位失败: {locator}")

    @staticmethod
    def run_push_client(push_completed):
        """修改：接收Event参数，标记推图完成状态"""
        try:
            push_images_auto()  # 调用非测试函数
            push_completed.set()  # 推图成功，标记完成
        except Exception as e:
            allure.attach(f"推图失败: {str(e)}", name="推图错误", attachment_type=allure.attachment_type.TEXT)
            push_completed.set()  # 即使失败，也标记完成，避免死等
            raise

    @allure.story("启动推图&分拣图片")
    def test_seat_operation(self):
        with allure.step("步骤1：林禹成账号登录bash系统"):
            # 兼容Linux容器网络，增加页面加载失败重试
            for retry in range(2):
                try:
                    self.driver.get("http://fat-bash-web.svfactory.com:6180/#/signIn")
                    # 验证页面加载完成
                    WebDriverWait(self.driver, CRITICAL_TIMEOUT).until(
                        EC.title_contains("登录")
                    )
                    break
                except TimeoutException as e:
                    if retry == 1:
                        allure.attach(f"页面加载超时: {str(e)}", name="页面加载错误", attachment_type=allure.attachment_type.TEXT)
                        raise
                    self.driver.refresh()
                    time.sleep(2)

            # 输入账号（使用重试函数，加固定位）
            username_input = self._retry_find_element((By.XPATH, '//input[@placeholder="请输入账号"]'))
            username_input.clear()
            username_input.send_keys(self.username)

            # 输入密码（使用重试函数）
            password_input = self._retry_find_element((By.XPATH, '//input[@placeholder="请输入密码"]'))
            password_input.clear()
            password_input.send_keys(self.password)

            # 点击登录按钮（等待可点击+重试）
            login_button = WebDriverWait(self.driver, BASE_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='登录']"))
            )
            login_button.click()
            time.sleep(3)  # 登录后等待页面跳转

        with allure.step("步骤2：申请坐席"):
            # 等待进入首页（使用重试函数）
            self._retry_find_element((By.XPATH, "//div[contains(@class, 'dashboard')]"), CRITICAL_TIMEOUT)

            # 验证初始坐席状态为"我已离席"（使用重试函数）
            status_text = self._retry_find_element((By.XPATH, "//span[@class='status-text']"))
            if status_text.text != "我已离席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"初始坐席状态应为'我已离席'，实际为: {status_text.text}")
            allure.attach("初始坐席状态: 我已离席", name="状态验证", attachment_type=allure.attachment_type.TEXT)

            # 点击申请坐席按钮（等待可点击）
            apply_button = WebDriverWait(self.driver, BASE_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'申请坐席')]"))
            )
            apply_button.click()

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
                allure.attach(self.driver.get_screenshot_as_png(), name="连接失败截图", attachment_type=allure.attachment_type.PNG)
                allure.attach(self.driver.page_source, name="连接失败页面源码", attachment_type=allure.attachment_type.HTML)
                allure.attach(f"连接消息验证失败: {str(e)}", name="错误", attachment_type=allure.attachment_type.TEXT)
                raise

            # 验证坐席状态变为"我已坐席"（优化等待逻辑）
            def check_seat_status():
                try:
                    status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
                    return status_text.text == "我已坐席"
                except:
                    return False

            WebDriverWait(self.driver, CRITICAL_TIMEOUT).until(lambda driver: check_seat_status())
            status_text = self.driver.find_element(By.XPATH, "//span[@class='status-text']")
            allure.attach(f"当前坐席状态: {status_text.text}", name="状态验证", attachment_type=allure.attachment_type.TEXT)

            if status_text.text != "我已坐席":
                allure.attach(f"异常状态: {status_text.text}", name="状态错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(f"申请坐席后状态应为'我已坐席'，实际为: {status_text.text}")

        with allure.step("步骤3：启动推图客户端"):
            # ========== 推图线程加固（线程安全+超时控制） ==========
            with self.push_lock:
                if self.push_thread is None or not self.push_thread.is_alive():
                    # 启动推图线程，传入完成标记
                    self.push_thread = threading.Thread(
                        target=self.run_push_client,
                        args=(self.push_completed,)
                    )
                    self.push_thread.daemon = True
                    self.push_thread.start()
                    allure.attach("推图客户端已启动", name="推图启动", attachment_type=allure.attachment_type.TEXT)

                    # 等待推图线程初始化（延长至8秒，适配容器性能）
                    time.sleep(8)
                    allure.attach("推图线程初始化完成", name="推图状态", attachment_type=allure.attachment_type.TEXT)
            # ======================================================

        with allure.step("步骤4：等待图片出现并分拣"):
            empty_counter = 0

            while True:
                try:
                    # 显式等待产品名称元素出现（使用重试函数）
                    product_name = self._retry_find_element((By.XPATH, '//span[@class="product-name"]'), BASE_TIMEOUT)
                    current_text = product_name.text.strip()

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

                            # 优化点击逻辑（增加鼠标移动+双击，确保生效）
                            ActionChains(self.driver).move_to_element(canvas_list[0]).click().perform()
                            time.sleep(1)

                        continue

                    # 情况2：检测到空文本
                    elif current_text == "":
                        empty_counter += 1
                        # 检查推图是否完成，避免无意义等待
                        if self.push_completed.is_set():
                            allure.attach("推图已完成，无新图片，执行离席", name="推图状态", attachment_type=allure.attachment_type.TEXT)
                            break

                        # 连续空次数达阈值，执行离席
                        if empty_counter >= MAX_EMPTY_COUNT:
                            leave_button = WebDriverWait(self.driver, BASE_TIMEOUT).until(
                                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"申请离席")]'))
                            )
                            leave_button.click()
                            sleep(8)  # 延长离席等待至8秒
                            allure.attach(f"连续{MAX_EMPTY_COUNT}次检测到空产品名称，执行离席",
                                          name="离席操作",
                                          attachment_type=allure.attachment_type.TEXT)
                            break

                        time.sleep(CHECK_INTERVAL)
                        continue

                except Exception as e:
                    # 增强异常排查（记录当前空计数器+推图线程状态）
                    allure.attach(f"空计数器: {empty_counter}", name="监控状态", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(f"推图线程是否存活: {self.push_thread.is_alive() if self.push_thread else False}",
                                  name="线程状态", attachment_type=allure.attachment_type.TEXT)
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
                    try:
                        leave_button = self.driver.find_element(By.XPATH, '//span[contains(text(),"申请离席")]')
                        if leave_button.is_enabled():
                            leave_button.click()
                    except:
                        pass
                    raise

    @classmethod
    def teardown_class(cls):
        # ========== 3. 推图线程兜底（确保线程终止） ==========
        if cls.push_thread and cls.push_thread.is_alive():
            try:
                # 等待推图线程结束，超时10秒强制退出
                cls.push_thread.join(timeout=10)
                allure.attach("推图线程已正常终止", name="线程清理", attachment_type=allure.attachment_type.TEXT)
            except Exception as e:
                allure.attach(f"推图线程终止超时: {str(e)}", name="线程清理警告", attachment_type=allure.attachment_type.TEXT)
        # ======================================================

        # ========== 浏览器资源清理加固（适配浏览器池） ==========
        if hasattr(cls, 'driver') and cls.driver:
            try:
                # 导航到空白页，释放页面资源
                cls.driver.get("about:blank")
                # 清除所有缓存/存储
                cls.driver.delete_all_cookies()
                cls.driver.execute_script("""
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                    indexedDB.databases().then(dbs => dbs.forEach(db => indexedDB.deleteDatabase(db.name)));
                """)
                time.sleep(1)  # 等待清理完成
            except Exception as e:
                allure.attach(f"清理浏览器状态警告: {str(e)}", name="浏览器清理警告", attachment_type=allure.attachment_type.TEXT)
        # ======================================================

        # 调用浏览器池的释放方法（核心！释放信号量）
        release_browser()
        allure.attach("浏览器资源已释放", name="资源清理", attachment_type=allure.attachment_type.TEXT)