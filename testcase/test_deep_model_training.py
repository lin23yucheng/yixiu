import re
import pytest
import allure
import time
from common.Request_Response import ApiClient
from common import Assert
from api import api_login, api_comprehensive_sample_library, api_deep_training_tasks

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


@allure.feature("场景：深度模型训练全流程")
class Test_deep_model_training:
    @classmethod
    def setup_class(cls):
        """初始化接口封装实例"""
        cls.api_comprehensive = api_comprehensive_sample_library.ApiComprehensiveSampleLibrary(global_client)
        cls.api_deep = api_deep_training_tasks.ApiDeepTrainTasks(global_client)
        cls.task_name = f"接口自动化-{time_str}"  # 统一任务名称格式
        cls.max_wait_seconds = 1800  # 最大等待30分钟
        cls.poll_interval = 10  # 轮询间隔10秒
        cls.start_timestamp = None  # 新增时间记录点
        cls.trainTaskId = None

    def _monitor_training_progress(self):
        """训练进度监控核心逻辑（含时间统计）"""
        start_time = time.time()
        self.start_timestamp = start_time  # 记录开始时间
        attempt = 0

        with allure.step("监控训练任务进度"):
            while True:
                attempt += 1
                with allure.step(f"第{attempt}次状态检查"):
                    # 发送查询请求
                    response = self.api_deep.query_train_tasks(self.task_name)
                    assertions.assert_code(response.status_code, 200)

                    # 解析响应数据
                    response_data = response.json()
                    tasks = response_data['data']['list']

                    # 记录原始响应
                    allure.attach(
                        str(response_data),
                        name="原始响应数据",
                        attachment_type=allure.attachment_type.JSON
                    )

                    # 验证任务存在
                    if not tasks:
                        pytest.fail(f"未找到任务: {self.task_name}")

                    # 获取任务状态
                    current_task = next(
                        (t for t in tasks if t['taskName'] == self.task_name),
                        None
                    )
                    if not current_task:
                        pytest.fail(f"任务列表匹配失败: {self.task_name}")

                    status = current_task['dataStatus']
                    self.trainTaskId = current_task['trainTaskId']
                    allure.attach(
                        f"当前状态: {status} (0=处理中, 1=完成, 2=异常)",
                        name="状态解析"
                    )
                    allure.attach(
                        f"trainTaskId: {self.trainTaskId}",
                        name="任务ID",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    # 新增时间统计部分
                    current_duration = int(time.time() - start_time)
                    mins, secs = divmod(current_duration, 60)
                    time_message = f"已等待时间：{mins}分{secs}秒"

                    # 记录到Allure
                    allure.attach(
                        time_message,
                        name="耗时统计",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    # 控制台实时打印（可选）
                    print(f"\rCurrent waiting time: {mins}m {secs}s", end="")

                    # 状态判断
                    if status == 1:
                        allure.attach("训练任务已完成", name="状态更新")
                        return True
                    elif status == 2:
                        pytest.fail(f"训练异常: {current_task.get('errorMsg', '处理异常')}")

                    # 超时检查
                    elapsed = time.time() - start_time
                    if elapsed > self.max_wait_seconds:
                        pytest.fail(f"训练超时: 等待{self.max_wait_seconds}秒未完成")

                    # 间隔等待
                    time.sleep(self.poll_interval)

    @allure.story("创建/追加深度训练任务并监控数据处理状态")
    def test_train_task_workflow(self):
        total_start = time.time()  # 记录总开始时间

        with allure.step("步骤1：创建深度训练任务"):
            response = self.api_comprehensive.create_deep_training_tasks(
                defectName=["shang"],
                photoId=["1", "2", "3"],
                cut=1024
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
            self._monitor_training_progress()

        with allure.step("步骤3：处理时间统计"):
            # 计算总耗时
            total_duration = int(time.time() - total_start)
            process_duration = int(time.time() - self.creation_time)

            # 格式化成可读时间
            def format_time(seconds):
                mins, secs = divmod(seconds, 60)
                hours, mins = divmod(mins, 60)
                return f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"

            # 添加到Allure报告
            allure.attach(
                f"总执行时间：{format_time(total_duration)}\n"
                f"纯处理等待时间：{format_time(process_duration)}",
                name="时间统计汇总",
                attachment_type=allure.attachment_type.TEXT
            )

            # 控制台打印
            print(f"\nTotal execution time: {format_time(total_duration)}")
            print(f"Pure processing time: {format_time(process_duration)}")

        with allure.step("步骤4：追加ok图"):
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

        with allure.step("步骤5：监控追加数据处理进度"):
            self._monitor_training_progress()

        with allure.step("步骤6：开始模型训练"):
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--alluredir=./allure-results'])
