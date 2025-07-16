"""
深度模型训练接口自动化流程
"""
import pytest
import allure
import time
import os
from configparser import ConfigParser
from common.Request_Response import ApiClient
from common import Assert
from api import api_login, api_comprehensive_sample_library, api_deep_training_tasks
from common.monitor_utils import MonitorUtils

assertions = Assert.Assertions()
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


@allure.feature("场景：深度模型训练全流程")
class TestDeepModelTraining:
    @classmethod
    def setup_class(cls):
        """初始化接口封装实例"""
        cls.api_comprehensive = api_comprehensive_sample_library.ApiComprehensiveSampleLibrary(global_client)
        cls.api_deep = api_deep_training_tasks.ApiDeepTrainTasks(global_client)
        cls.api_model = api_deep_training_tasks.ApiModelTrain(global_client)
        cls.task_name = f"接口自动化-{time_str}-目标检测"  # 统一任务名称格式
        cls.max_wait_seconds = 1800  # 最大等待30分钟
        cls.poll_interval = 10  # 轮询间隔10秒
        cls.start_timestamp = None  # 新增时间记录点
        cls.trainTaskId = None
        cls.modelTrainId = None
        cls.monitor = MonitorUtils(api_deep=cls.api_deep, api_model=cls.api_model)

    def teardown_class(cls):
        """将生成的ID写入配置文件"""
        if not cls.trainTaskId or not cls.modelTrainId:
            print("警告：任务ID或模型ID未获取到，可能流程未完成")
            return

        config_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # 向上一级，回到项目根目录
            'config/env_config.ini'  # 根目录下的 config 目录
        ))

        config = ConfigParser()
        config.read(config_path)

        if not config.has_section('persistent_ids'):
            config.add_section('persistent_ids')

        config.set('persistent_ids', 'train_task_id', str(cls.trainTaskId))
        config.set('persistent_ids', 'model_train_id', str(cls.modelTrainId))

        with open(config_path, 'w') as f:
            config.write(f)
        print(f"已写入配置文件：{config_path}")

    @allure.story("目标检测/分割模型训练&提交")
    def test_deep_task_workflow(self):
        total_start = time.time()  # 记录总开始时间

        with allure.step("步骤1：创建深度训练任务"):
            self.cut_value = 1024
            response = self.api_comprehensive.create_deep_training_tasks(
                defectName=["shang"],
                photoId=["1", "2", "3"],
                cut=self.cut_value,
                taskName=self.task_name,
                classifyType=[],
                caseId="detection",
                caseName="目标检测/分割",
                type=1,
                iscut=True
            )

            # 验证初始响应
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 记录任务信息
            allure.attach(
                f"任务名称: {self.task_name}",
                name="任务创建信息",
                attachment_type=allure.attachment_type.TEXT
            )
            self.creation_time = time.time()  # 记录任务创建完成时间

        with allure.step("步骤2：监控创建数据处理进度"):
            self.trainTaskId, success = self.monitor.monitor_cut_progress(
                self.task_name,
                "目标检测/分割切图处理"
            )
            self.__class__.trainTaskId = self.trainTaskId

        with allure.step("步骤3：追加ok图"):
            if not self.trainTaskId:
                pytest.fail("trainTaskId未被正确获取，请检查监控方法")
            response = self.api_comprehensive.append_deep_training_tasks2(
                defectName=None,
                photoId=["3"],
                sampleType=["ok"],
                trainId=self.trainTaskId,
                datasetType=1
            )

            # 验证初始响应
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

        with allure.step("步骤4：监控追加数据处理进度"):
            self.trainTaskId, success = self.monitor.monitor_cut_progress(
                self.task_name,
                "目标检测/分割追加OK图处理"
            )
            self.__class__.trainTaskId = self.trainTaskId

        with allure.step("步骤5：开始模型训练"):
            # -------------------- 查询模型方案 --------------------
            with allure.step("子步骤1：查询模型方案获取caseId"):
                model_response = self.api_model.query_model()
                assertions.assert_code(model_response.status_code, 200)
                model_data = model_response.json()
                assertions.assert_in_text(model_data['msg'], '操作成功')

                # 解析case映射关系
                cut_case_mapping = {
                    768: "DetS V2 实例分割",
                    1024: "Det V2 目标检测",
                    2048: "Det V1 目标检测"
                }
                if self.cut_value not in cut_case_mapping:
                    pytest.fail(f"Invalid cut value: {self.cut_value}, expected 1024/768/2048")
                target_case_name = cut_case_mapping[self.cut_value]

                # 查找匹配的case
                matched_case = next(
                    (case for case in model_data['data'] if case['caseName'] == target_case_name),
                    None
                )
                if not matched_case:
                    pytest.fail(f"Case '{target_case_name}' not found in model response")
                case_id = matched_case['caseId']

                allure.attach(
                    f"Selected caseId: {case_id} (cut={self.cut_value})",
                    name="Model Case Selection",
                    attachment_type=allure.attachment_type.TEXT
                )

            # -------------------- 查询训练机器 --------------------
            with allure.step("子步骤2：查询训练机器获取computingPowerId"):
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

            # -------------------- 开始深度模型训练 --------------------
            with allure.step("子步骤3：组装参数并开始训练"):
                train_response = self.api_model.start_train(case_id, -1, computing_power_id, self.trainTaskId, "", "",
                                                            "1704414001586651234", 30)
                assertions.assert_code(train_response.status_code, 200)
                train_data = train_response.json()
                assertions.assert_in_text(train_data['msg'], '操作成功')

        with allure.step("步骤6：监控训练进度"):
            self.modelTrainId, success = self.monitor.monitor_train_progress(self.trainTaskId,"YoloV8目标检测训练")
            self.__class__.modelTrainId = self.modelTrainId
            time.sleep(3)

        with allure.step("步骤7：提交模型"):
            # 提交模型
            with allure.step("子步骤1：发起模型提交"):
                submit_response = self.api_model.submit_model(
                    modelName=self.task_name,
                    modelTrainId=self.modelTrainId
                )
                assertions.assert_code(submit_response.status_code, 200)
                submit_data = submit_response.json()
                assertions.assert_in_text(submit_data['msg'], '操作成功')

                allure.attach(
                    f"提交的模型名称: {self.task_name}",
                    name="模型提交信息",
                    attachment_type=allure.attachment_type.TEXT
                )

            # 监控提交状态
            with allure.step("子步骤2：监控模型提交状态"):
                success = self.monitor.monitor_commit_progress(self.trainTaskId,"YoloV8目标检测模型提交")

            # 最终成功提示
        allure.dynamic.description(
            "深度模型训练（目标检测）测试完成！\n"
            f"总耗时: {time.strftime('%H:%M:%S', time.gmtime(time.time() - total_start))}"
        )
        print("\n\n\033[92m深度目标检测模型训练-自动化流程测试完成！\033[0m")
        print(f"总耗时: {time.strftime('%H:%M:%S', time.gmtime(time.time() - total_start))}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--alluredir=./allure-results'])
