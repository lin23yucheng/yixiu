"""
检测模型训练指标与之前一致
"""
import pytest
import allure
import time
import os
import json
from configparser import ConfigParser
from common.Request_Response import ApiClient
from common import Assert
from api import api_login, api_deep_training_tasks
from common.monitor_utils import MonitorUtils

assertions = Assert.Assertions()

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


@pytest.fixture(scope="function")
def get_persistent_ids():
    """从配置文件中读取ID"""
    # 构建配置文件路径
    config_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # 向上一级，回到项目根目录
        'config/env_config.ini'  # 根目录下的 config 目录
    ))

    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        pytest.skip("配置文件不存在")

    # 初始化ConfigParser并读取配置文件
    config = ConfigParser()
    config.read(config_path)

    # 获取配置文件中的ID值
    ids = {
        'train_task_id': config.get('old_ids', 'train_task_id', fallback=None),
    }

    # 检查是否有任何ID值为None
    if None in ids.values():
        pytest.skip("训练任务ID未就绪")
    return ids


@allure.feature("场景：综合-检测实例分割YoloV8模型训练指标")
class TestModelTrainingMetrics:
    @classmethod
    def setup_class(cls):
        """初始化接口封装实例"""
        cls.api_model = api_deep_training_tasks.ApiModelTrain(global_client)
        cls.api_deep = api_deep_training_tasks.ApiDeepTrainTasks(global_client)
        cls.max_wait_seconds = 1800  # 最大等待30分钟
        cls.poll_interval = 10  # 轮询间隔10秒
        cls.trainTaskId = None
        cls.monitor = MonitorUtils(api_deep=cls.api_deep, api_model=cls.api_model)

    # def _monitor_train_progress(self):
    #     """模型训练状态监控"""
    #     start_time = time.time()
    #     attempt = 0
    #
    #     with allure.step("监控模型训练与验证状态"):
    #         while True:
    #             attempt += 1
    #             with allure.step(f"第{attempt}次训练状态检查"):
    #                 # 发送查询请求
    #                 response = self.api_model.query_train_records(self.trainTaskId)
    #                 assertions.assert_code(response.status_code, 200)
    #
    #                 # 解析响应数据
    #                 response_data = response.json()
    #                 records = response_data['data']['list']
    #
    #                 # 记录原始响应到Allure
    #                 allure.attach(
    #                     str(response_data),
    #                     name="训练记录响应数据",
    #                     attachment_type=allure.attachment_type.JSON
    #                 )
    #
    #                 # 验证记录存在性
    #                 if not records:
    #                     pytest.fail(f"未找到trainTaskId={self.trainTaskId}的训练记录")
    #
    #                 current_record = records[0]  # 取第一条记录
    #                 train_status = current_record['trainStatus']
    #                 verify_status = current_record.get('verifyStatus', None)
    #                 self.modelTrainId = current_record['modelTrainId']
    #                 self.__class__.modelTrainId = current_record['modelTrainId']  # 关键：赋值给类变量
    #
    #                 # 时间统计
    #                 current_duration = int(time.time() - start_time)
    #                 mins, secs = divmod(current_duration, 60)
    #                 time_message = f"训练等待时间：{mins}分{secs}秒"
    #
    #                 # 状态信息汇总
    #                 status_info = (
    #                     f"\ntrainStatus={train_status} "
    #                     f"(0=训练中,1=训练失败,2=训练完成,3=打包中,4=排队中,5=转onnx中,6=转triton中)\n"
    #                     f"verifyStatus={verify_status} "
    #                     f"(0=未验证,1=验证中,2=验证失败,3=验证成功)\n"
    #                     f"{time_message}\n"
    #                     f"-------------------------------\n"
    #                 )
    #                 allure.attach(status_info, name="状态详情")
    #
    #                 # 控制台实时打印
    #                 print(f"训练/验证状态: {status_info}", end="")
    #
    #                 # 状态机判断
    #                 if train_status == 1:
    #                     pytest.fail("训练失败，请检查日志")
    #                 elif train_status == 2:
    #                     if verify_status == 2:
    #                         pytest.fail("验证失败，请检查日志")
    #                     elif verify_status == 3:
    #                         allure.attach("训练&验证已完成", name="最终状态")
    #                         return True  # 符合继续执行的条件
    #
    #                 # 超时检查（30分钟）
    #                 elapsed = time.time() - start_time
    #                 if elapsed > self.max_wait_seconds:
    #                     pytest.fail(f"训练卡住，请检查日志（等待超过{self.max_wait_seconds}秒）")
    #
    #                 # 间隔等待
    #                 time.sleep(self.poll_interval)

    @allure.story("验证模型训练前后指标一致")
    def test_model_train_metrics(self, get_persistent_ids):
        """验证模型训练指标在多次训练后保持一致"""
        allure.dynamic.title(f"训练任务指标验证 (ID: {get_persistent_ids['train_task_id']})")
        total_start = time.time()

        # 设置训练任务ID
        self.__class__.trainTaskId = get_persistent_ids['train_task_id']

        # 封装训练记录获取函数
        def get_train_records():
            """获取并验证训练记录"""
            response = self.api_model.query_train_records(self.trainTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            return response_data['data']['list']

        with allure.step("步骤1：开始模型训练"):
            with allure.step("子步骤1：查询训练机器获取computingPowerId"):
                machine_response = self.api_model.query_machine()
                assertions.assert_code(machine_response.status_code, 200)
                machine_data = machine_response.json()
                assertions.assert_in_text(machine_data['msg'], '操作成功')

                # 查找测试机器
                test_machine = next(
                    (machine for machine in machine_data['data'] if machine['name'] == '测试机器'),
                    None
                )
                if not test_machine:
                    pytest.fail("测试机器 not found in machine list")
                computing_power_id = test_machine['computingPowerId']

                allure.attach(
                    f"Found computingPowerId: {computing_power_id}",
                    name="Training Machine ID",
                    attachment_type=allure.attachment_type.TEXT
                )

            with allure.step("子步骤2：组装参数并开始训练"):
                train_response = self.api_model.start_train(
                    "official_yolov8_seg_model",
                    -1,
                    computing_power_id,
                    self.trainTaskId,
                    "",
                    "",
                    "1704414001586651237",
                    50
                )
                assertions.assert_code(train_response.status_code, 200)
                train_data = train_response.json()
                assertions.assert_in_text(train_data['msg'], '操作成功')

        with allure.step("步骤2：监控训练进度"):
            try:
                _, success = self.monitor.monitor_train_progress(self.trainTaskId,"YoloV8实例分割训练")
            except Exception as e:
                allure.attach(f"训练监控失败: {str(e)}", name="错误详情")
                pytest.fail(f"训练监控过程中发生错误: {str(e)}")

        with allure.step("步骤3：对比训练指标"):
            try:
                records = get_train_records()

                # 健壮性检查
                if not records:
                    pytest.fail("未找到任何训练记录")
                if len(records) < 2:
                    pytest.skip(f"训练记录不足2条，无法进行指标对比（当前记录数：{len(records)}）")

                # 提取关键记录
                latest_record = records[0]
                oldest_record = records[-1]

                # 获取训练指标并处理可能的格式问题
                def parse_indicators(indicators):
                    """处理多种可能的指标格式"""
                    # 如果已经是字典，直接返回
                    if isinstance(indicators, dict):
                        return indicators

                    # 如果是字符串，尝试解析为JSON
                    if isinstance(indicators, str):
                        try:
                            return json.loads(indicators)
                        except json.JSONDecodeError:
                            # 如果解析失败，尝试作为普通字符串处理
                            return {"raw_value": indicators}

                    # 如果是其他类型，转换为字符串
                    return {"raw_value": str(indicators)}

                latest_indicators = parse_indicators(latest_record.get('trainIndicators', {}))
                oldest_indicators = parse_indicators(oldest_record.get('trainIndicators', {}))

                # 记录原始指标值到Allure
                allure.attach(
                    f"原始最新指标值: {latest_record.get('trainIndicators')}\n"
                    f"原始历史指标值: {oldest_record.get('trainIndicators')}",
                    name="原始指标数据",
                    attachment_type=allure.attachment_type.TEXT
                )

                # 格式化指标输出
                def format_metrics(metrics):
                    return "\n".join([f"{k}: {v}" for k, v in metrics.items()]) or "无指标数据"

                # 优化报告展示
                with allure.step("训练指标详情"):
                    allure.attach(
                        f"最新训练指标:\n{format_metrics(latest_indicators)}\n\n"
                        f"历史训练指标:\n{format_metrics(oldest_indicators)}",
                        name="指标对比",
                        attachment_type=allure.attachment_type.TEXT
                    )

                # 指标对比逻辑
                if latest_indicators == oldest_indicators:
                    allure.attach("✅ 训练指标前后一致", name="测试结果")
                    print("训练指标验证通过")
                else:
                    # 生成差异报告
                    diff_details = [
                        f"指标 '{key}': 最新值={latest_indicators.get(key, 'N/A')}, "
                        f"历史值={oldest_indicators.get(key, 'N/A')}"
                        for key in set(latest_indicators.keys()) | set(oldest_indicators.keys())
                        if latest_indicators.get(key) != oldest_indicators.get(key)
                    ]

                    # 添加可视化差异报告
                    diff_report = "指标差异详情:\n" + "\n".join(diff_details) or "所有指标值均存在差异"
                    allure.attach(diff_report, name="指标差异", attachment_type=allure.attachment_type.TEXT)

                    # 抛出异常
                    pytest.fail("❌ 模型训练指标前后不一致")

            except Exception as e:
                allure.attach(f"指标对比失败: {str(e)}", name="错误详情")
                pytest.fail(f"指标对比过程中发生错误: {str(e)}")

        # 添加总耗时统计
        total_duration = time.time() - total_start
        mins, secs = divmod(total_duration, 60)
        allure.attach(
            f"测试总耗时: {int(mins)}分{int(secs)}秒",
            name="性能统计",
            attachment_type=allure.attachment_type.TEXT
        )
