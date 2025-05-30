import os
import time
import pytest
import allure
from common import Assert
from configparser import ConfigParser
from common.Request_Response import ApiClient
from api import api_login, api_deep_training_tasks

assertions = Assert.Assertions()
env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


@pytest.fixture(scope="session")
def get_persistent_ids():
    """从配置文件中读取ID"""
    config_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # 向上一级，回到项目根目录
        'config/env_config.ini'  # 根目录下的 config 目录
    ))

    if not os.path.exists(config_path):
        pytest.skip("配置文件不存在")

    config = ConfigParser()
    config.read(config_path)

    # 获取值
    ids = {
        'train_task_id': config.get('persistent_ids', 'train_task_id', fallback=None),
        'model_train_id': config.get('persistent_ids', 'model_train_id', fallback=None)
    }

    # 空值检查
    if None in ids.values():
        pytest.skip("训练任务ID未就绪")
    return ids


@allure.feature("场景：深度模型后处理全流程")
class Test_post_process:
    @classmethod
    def setup_class(cls):
        """初始化接口封装实例"""
        cls.api_deep = api_deep_training_tasks.ApiDeepTrainTasks(global_client)
        cls.api_model = api_deep_training_tasks.ApiModelTrain(global_client)
        cls.api_process = api_deep_training_tasks.ApiPostProcess(global_client)
        cls.task_name = f"接口自动化-{time_str}"
        cls.max_wait_seconds = 1800  # 最大等待30分钟
        cls.poll_interval = 5  # 轮询间隔5秒
        cls.start_timestamp = None  # 新增时间记录点
        cls.trainTaskId = None
        cls.verifyId = None

    def _monitor_report_analysis_progress(self):
        """报表分析状态监控"""
        start_time = time.time()  # 记录开始时间
        attempt = 0  # 初始化尝试次数

        with allure.step("监控报表分析状态"):  # Allure报告步骤：监控报表分析状态
            while True:  # 循环直到条件满足或超时
                attempt += 1  # 增加尝试次数
                with allure.step(f"第{attempt}次提交状态检查"):  # Allure报告步骤：第X次提交状态检查
                    # 发送查询请求以获取报表分析状态
                    response = self.api_process.report_analysis_status(self.verifyId)
                    assertions.assert_code(response.status_code, 200)  # 断言响应状态码为200

                    # 解析响应数据为JSON格式
                    response_data = response.json()
                    # 检查响应数据中的'data'字段是否存在且为字典类型
                    data = response_data.get('data')
                    if not isinstance(data, dict):
                        allure.attach(f"响应中data字段格式错误: {response_data}", name="错误详情")  # 将错误详情附加到Allure报告
                        pytest.fail("接口返回data字段格式不符合预期")  # 测试失败并提供错误信息

                    # 从'data'字典中获取'subStatus'字段
                    subStatus = data.get('subStatus')

                    # 将原始响应数据附加到Allure报告
                    allure.attach(
                        str(response_data),
                        name="提交状态响应数据",
                        attachment_type=allure.attachment_type.JSON
                    )

                    # 计算当前持续时间并格式化为分钟和秒
                    current_duration = int(time.time() - start_time)
                    mins, secs = divmod(current_duration, 60)
                    time_message = f"报表分析等待时间：{mins}分{secs}秒"

                    # 汇总状态信息，包括subStatus和等待时间
                    status_info = (
                        f"\nsubStatus={subStatus} "
                        f"(1=分析中,2=分析完成)\n"
                        f"{time_message}\n"
                        f"-------------------------------\n"
                    )
                    allure.attach(status_info, name="报表分析状态详情")  # 将状态信息附加到Allure报告

                    # 在控制台实时打印报表分析状态
                    print(f"报表分析状态: {status_info}", end="")

                    # 根据subStatus判断当前状态
                    if subStatus == 2:
                        allure.attach("报表分析已完成", name="最终状态")  # 将最终状态附加到Allure报告
                        time.sleep(3)  # 等待3秒
                        return True  # 返回True表示分析完成
                    elif subStatus == 1:
                        pass  # 继续循环，表示仍在分析中
                    else:
                        pytest.fail(f"未知状态码: {subStatus}")  # 测试失败，未知状态码

                    # 检查是否超时（30分钟）
                    elapsed = time.time() - start_time
                    if elapsed > self.max_wait_seconds:
                        pytest.fail(f"报表分析卡住，请检查日志（等待超过{self.max_wait_seconds}秒)")  # 测试失败，超时

                    # 等待指定的时间间隔后继续下一次检查
                    time.sleep(self.poll_interval)



    def _monitor_sample_analysis_progress(self):
        """样本分析状态监控"""
        start_time = time.time()
        attempt = 0

        with allure.step("监控样本分析状态"):
            while True:
                attempt += 1
                with allure.step(f"第{attempt}次提交状态检查"):
                    # 发送查询请求
                    response = self.api_process.sample_analysis_status(self.verifyId)
                    assertions.assert_code(response.status_code, 200)

                    # 解析响应数据
                    response_data = response.json()
                    # 检查data字段是否存在且为字典类型
                    data = response_data.get('data')
                    if not isinstance(data, dict):
                        allure.attach(f"响应中data字段格式错误: {response_data}", name="错误详情")
                        pytest.fail("接口返回data字段格式不符合预期")

                        # 从嵌套结构中获取subStatus
                    subStatus = data.get('subStatus')

                    # 记录原始响应到Allure
                    allure.attach(
                        str(response_data),
                        name="样本分析响应数据",
                        attachment_type=allure.attachment_type.JSON
                    )

                    # 时间统计
                    current_duration = int(time.time() - start_time)
                    mins, secs = divmod(current_duration, 60)
                    time_message = f"样本分析等待时间：{mins}分{secs}秒"

                    # 状态信息汇总
                    status_info = (
                        f"\nsubStatus={subStatus} "
                        f"(1=分析中,2=分析完成)\n"
                        f"{time_message}\n"
                        f"-------------------------------\n"
                    )
                    allure.attach(status_info, name="样本分析状态详情")

                    # 控制台实时打印
                    print(f"样本分析状态: {status_info}", end="")

                    # 状态判断
                    if subStatus == 2:
                        allure.attach("样本分析已完成", name="最终状态")
                        time.sleep(3)
                        return True
                    elif subStatus == 1:
                        pass  # 继续循环
                    else:
                        pytest.fail(f"未知状态码: {subStatus}")

                    # 超时检查（30分钟）
                    elapsed = time.time() - start_time
                    if elapsed > self.max_wait_seconds:
                        pytest.fail(f"样本分析卡住，请检查日志（等待超过{self.max_wait_seconds}秒）")

                    # 间隔等待
                    time.sleep(self.poll_interval)

    @allure.story("深度模型报表&样本分析")
    def test_analysis(self, get_persistent_ids):  # 注入fixture
        train_task_id = get_persistent_ids['train_task_id']  # 从配置获取ID
        self.__class__.trainTaskId = get_persistent_ids['train_task_id']  # 关键：赋值给类变量

        with allure.step("步骤1：训练记录查询获取训练集的verifyId"):
            # 使用配置中的train_task_id发起请求
            response = self.api_model.query_train_records(
                trainTaskId=train_task_id
            )

            # 响应断言
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 提取训练集verify_id
            # verify_id = None
            for task in response_data.get('data', {}).get('list', []):
                # 遍历verifyRecord查找包含'训练集'的条目
                for record in task.get('verifyRecord', []):
                    if '训练集' in record.get('name', ''):
                        verify_id = record.get('id')
                        self.__class__.verifyId = verify_id  # 关键：赋值给类变量
                        break
                if verify_id:
                    break

            # 确保找到有效ID
            assertions.assert_is_not_none(
                self.verifyId,
                f"未找到训练集verifyRecordID，响应数据：{response_data}"
            )

            allure.attach(
                f"训练集验证id: {self.verifyId}",
                name="训练集-verifyId",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("步骤2：报表分析"):

            with allure.step("子步骤1：提交报表分析"):
                response = self.api_process.report_analysis(
                    verifyId=self.verifyId
                )

                # 响应断言
                assertions.assert_code(response.status_code, 200)
                response_data = response.json()
                assertions.assert_in_text(response_data['msg'], '成功')

                allure.attach(
                    f"提交报表分析id: {self.verifyId}",
                    name="报表分析信息",
                    attachment_type=allure.attachment_type.TEXT
                )

            # 监控报表分析状态
            with allure.step("子步骤2：监控报表分析状态"):
                self._monitor_report_analysis_progress()

        with allure.step("步骤3：样本分析"):

            with allure.step("子步骤1：提交样本分析"):
                response = self.api_process.sample_analysis(
                    verifyId=self.verifyId
                )

                # 响应断言
                assertions.assert_code(response.status_code, 200)
                response_data = response.json()
                assertions.assert_in_text(response_data['msg'], '成功')

                allure.attach(
                    f"提交样本分析id: {self.verifyId}",
                    name="样本分析信息",
                    attachment_type=allure.attachment_type.TEXT
                )

            # 监控样本分析状态
            with allure.step("子步骤2：监控报表分析状态"):
                self._monitor_sample_analysis_progress()
