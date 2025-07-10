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

    # def _monitor_cut_progress(self):
    #     """数据处理状态监控"""
    #     start_time = time.time()
    #     self.start_timestamp = start_time  # 记录开始时间
    #     attempt = 0
    #
    #     with allure.step("监控训练任务进度"):
    #         while True:
    #             attempt += 1
    #             with allure.step(f"第{attempt}次状态检查"):
    #                 # 发送查询请求
    #                 response = self.api_deep.query_train_tasks(self.task_name)
    #                 assertions.assert_code(response.status_code, 200)
    #
    #                 # 解析响应数据
    #                 response_data = response.json()
    #                 tasks = response_data['data']['list']
    #
    #                 # 记录原始响应
    #                 allure.attach(
    #                     str(response_data),
    #                     name="原始响应数据",
    #                     attachment_type=allure.attachment_type.JSON
    #                 )
    #
    #                 # 验证任务存在
    #                 if not tasks:
    #                     pytest.fail(f"未找到任务: {self.task_name}")
    #
    #                 # 获取任务状态
    #                 current_task = next(
    #                     (t for t in tasks if t['taskName'] == self.task_name),
    #                     None
    #                 )
    #                 if not current_task:
    #                     pytest.fail(f"任务列表匹配失败: {self.task_name}")
    #
    #                 status = current_task['dataStatus']
    #                 self.trainTaskId = current_task['trainTaskId']
    #                 self.__class__.trainTaskId = current_task['trainTaskId']  # 关键：赋值给类变量
    #
    #                 allure.attach(
    #                     f"当前状态: {status} (0=处理中, 1=完成, 2=异常)",
    #                     name="状态解析"
    #                 )
    #                 allure.attach(
    #                     f"trainTaskId: {self.trainTaskId}",
    #                     name="任务ID",
    #                     attachment_type=allure.attachment_type.TEXT
    #                 )
    #
    #                 # 新增时间统计部分
    #                 current_duration = int(time.time() - start_time)
    #                 mins, secs = divmod(current_duration, 60)
    #                 time_message = f"处理已等待时间：{mins}分{secs}秒"
    #
    #                 # 记录到Allure
    #                 allure.attach(
    #                     time_message,
    #                     name="耗时统计",
    #                     attachment_type=allure.attachment_type.TEXT
    #                 )
    #
    #                 # 控制台实时打印
    #                 print(f"\r数据处理时间: {mins}m {secs}s", end="")
    #
    #                 # 状态判断
    #                 if status == 1:
    #                     allure.attach("训练任务已完成", name="状态更新")
    #                     print("\n数据处理已完成")
    #                     return True
    #                 elif status == 2:
    #                     pytest.fail(f"训练异常: {current_task.get('errorMsg', '处理异常')}")
    #
    #                 # 超时检查
    #                 elapsed = time.time() - start_time
    #                 if elapsed > self.max_wait_seconds:
    #                     pytest.fail(f"训练超时: 等待{self.max_wait_seconds}秒未完成")
    #
    #                 # 间隔等待
    #                 time.sleep(self.poll_interval)
    #
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
    #
    # def _monitor_commit_progress(self):
    #     """模型提交状态监控"""
    #     start_time = time.time()
    #     attempt = 0
    #
    #     with allure.step("监控模型提交状态"):
    #         while True:
    #             attempt += 1
    #             with allure.step(f"第{attempt}次提交状态检查"):
    #                 # 发送查询请求（复用训练记录接口）
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
    #                     name="提交状态响应数据",
    #                     attachment_type=allure.attachment_type.JSON
    #                 )
    #
    #                 # 验证记录存在性
    #                 if not records:
    #                     pytest.fail(f"未找到trainTaskId={self.trainTaskId}的提交记录")
    #
    #                 current_record = records[0]  # 取第一条记录
    #                 commit_status = current_record.get('commitStatus')
    #
    #                 # 时间统计
    #                 current_duration = int(time.time() - start_time)
    #                 mins, secs = divmod(current_duration, 60)
    #                 time_message = f"提交等待时间：{mins}分{secs}秒"
    #
    #                 # 状态信息汇总
    #                 status_info = (
    #                     f"\ncommitStatus={commit_status} "
    #                     f"(0=未提交,1=已提交,2=提交中,3=提交失败)\n"
    #                     f"{time_message}\n"
    #                     f"-------------------------------\n"
    #                 )
    #                 allure.attach(status_info, name="提交状态详情")
    #
    #                 # 控制台实时打印
    #                 print(f"提交状态: {status_info}", end="")
    #
    #                 # 状态机判断
    #                 if commit_status == 3:
    #                     pytest.fail("提交失败，请检查日志")
    #                 elif commit_status == 1:
    #                     allure.attach("模型提交已完成", name="最终状态")
    #                     return True
    #
    #                 # 超时检查（30分钟）
    #                 elapsed = time.time() - start_time
    #                 if elapsed > self.max_wait_seconds:
    #                     pytest.fail(f"提交卡住，请检查日志（等待超过{self.max_wait_seconds}秒）")
    #
    #                 # 间隔等待
    #                 time.sleep(self.poll_interval)

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
