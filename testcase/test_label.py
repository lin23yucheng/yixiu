"""
单产品-标注流程
"""
import os
import pytest
import allure
import psycopg2
import configparser
import time
from common import Assert
from datetime import datetime, timedelta
from common.Request_Response import ApiClient
from api import api_login, api_bash_sample_library, api_2D_label

assertions = Assert.Assertions()
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


@allure.feature("场景：分拣&标注全流程")
class TestLabel:
    @classmethod
    def setup_class(cls):
        """初始化接口封装实例"""
        cls.api_bash_sample = api_bash_sample_library.ApiBashSample(global_client)
        cls.api_2d_label = api_2D_label.Api2DLabel(global_client)
        cls.task_name = None
        cls.sampleDataSyncId_1 = None
        cls.sampleDataSyncId_2 = None
        cls.sampleDataSyncId_3 = None
        cls.dimensionTaskId = None
        cls.datasetDataId_1 = None
        cls.datasetDataId_2 = None

    def verify_task_status(self, expected_status, status_name):
        """
        验证标注任务状态是否符合预期
        """
        # 查询任务状态
        response = self.api_2d_label.query_2d_task(self.task_name)
        assertions.assert_code(response.status_code, 200)
        response_data = response.json()
        assertions.assert_in_text(response_data['msg'], '成功')

        # 查找指定任务
        task_list = response_data.get('data', {}).get('list', [])
        target_task = None
        for task in task_list:
            if task.get('taskName') == self.task_name:
                target_task = task
                break

        if target_task:
            current_status = target_task.get('taskStatus')
            # 记录状态信息到报告
            status_info = (
                f"任务名称: {self.task_name}\n"
                f"当前状态: {current_status} ({self.get_status_name(current_status)})\n"
                f"预期状态: {expected_status} ({status_name})"
            )
            allure.attach(status_info,
                          name="任务状态检查",
                          attachment_type=allure.attachment_type.TEXT)

            if current_status == expected_status:
                allure.attach(f"状态验证成功: 当前状态符合预期({status_name})",
                              name="状态验证结果",
                              attachment_type=allure.attachment_type.TEXT)
                return True
            else:
                error_msg = f"错误: 状态不符合预期！当前状态: {self.get_status_name(current_status)}，预期状态: {status_name}"
                allure.attach(error_msg,
                              name="状态验证失败",
                              attachment_type=allure.attachment_type.TEXT)
                pytest.fail(error_msg)
        else:
            error_msg = f"错误: 未找到任务名称为 '{self.task_name}' 的任务"
            allure.attach(error_msg,
                          name="任务查找失败",
                          attachment_type=allure.attachment_type.TEXT)
            pytest.fail(error_msg)

    def get_status_name(self, status_code):
        status_map = {
            1: "未开始",
            2: "进行中",
            3: "待复核",
            4: "复核通过",
            5: "已提交",
            7: "待重标",
            8: "复核未通过",
            9: "辅助标注中",
            10: "辅助标注完成"
        }
        return status_map.get(status_code, f"未知状态({status_code})")

    @pytest.mark.order(1)
    @allure.story("bash样本库分拣")
    def test_bash_sorting(self):
        # 计算日期参数
        current_date = datetime.now()
        endDateTime = current_date.strftime("%Y-%m-%d")
        startDateTime = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

        with allure.step("步骤1：查询bash样本库-原始样本") as step1:
            # 记录日期参数到Allure
            allure.attach(f"查询参数:\nstartDateTime={startDateTime}\nendDateTime={endDateTime}",
                          name="查询参数",
                          attachment_type=allure.attachment_type.TEXT)

            response = self.api_bash_sample.query_bash_sample(startDateTime, endDateTime)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 提取前三条数据的sampleDataSyncId
            sample_list = response_data.get('data', {}).get('list', [])
            if len(sample_list) >= 3:
                # 赋值给类变量
                TestLabel.sampleDataSyncId_1 = sample_list[0].get('sampleDataSyncId')
                TestLabel.sampleDataSyncId_2 = sample_list[1].get('sampleDataSyncId')
                TestLabel.sampleDataSyncId_3 = sample_list[2].get('sampleDataSyncId')

                # 记录提取的数据到Allure报告
                extracted_data = (
                    f"提取的前三条sampleDataSyncId:\n"
                    f"1. {TestLabel.sampleDataSyncId_1}\n"
                    f"2. {TestLabel.sampleDataSyncId_2}\n"
                    f"3. {TestLabel.sampleDataSyncId_3}"
                )
                allure.attach(extracted_data,
                              name="提取的sampleDataSyncId",
                              attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach("警告: 响应数据不足3条，无法提取全部ID",
                              name="数据提取警告",
                              attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤2：bash分拣") as step2:
            # 定义分拣任务列表: (sampleDataSyncId, 分拣结果只能是"ok"或"ng")
            sorting_tasks = [
                (self.sampleDataSyncId_1, "ng"),
                (self.sampleDataSyncId_2, "ng"),
                (self.sampleDataSyncId_3, "ok")
            ]

            # 遍历任务列表执行分拣
            for idx, (sample_id, label) in enumerate(sorting_tasks, 1):
                # 使用allure子步骤记录每个分拣任务
                with allure.step(f"分拣任务{idx}: sampleDataSyncId={sample_id}, label={label}"):
                    response = self.api_bash_sample.bash_sorting_sample(sample_id, label)
                    assertions.assert_code(response.status_code, 200)
                    response_data = response.json()
                    assertions.assert_in_text(response_data['msg'], '成功')

                    # 记录分拣结果到报告
                    allure.attach(
                        f"样本ID: {sample_id}\n分拣结果: {label}\n响应消息: {response_data['msg']}",
                        name=f"分拣任务{idx}结果",
                        attachment_type=allure.attachment_type.TEXT
                    )

        with allure.step("步骤3：创建标注任务") as step3:
            taskname = f"接口自动化标注-{time_str}"
            # 记录任务创建参数
            task_params = (
                f"任务名称: {taskname}\n"
                f"样本ID: {self.sampleDataSyncId_1}\n"
            )
            allure.attach(task_params, name="创建标注任务参数", attachment_type=allure.attachment_type.TEXT)

            response = self.api_bash_sample.create_label_task([self.sampleDataSyncId_1], startDateTime, endDateTime,
                                                              taskname)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')
            TestLabel.task_name = f"{taskname}-1"

        with allure.step("步骤4：查询标注任务的dimensionTaskId") as step4:
            response = self.api_bash_sample.query_append_task_id()
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 提取任务列表
            task_list = response_data.get('data', [])
            dimension_task_id = None

            # 查找匹配的任务
            for task in task_list:
                if task.get('name') == self.task_name:
                    dimension_task_id = task.get('code')
                    break

            # 处理结果
            if dimension_task_id:
                # 赋值给类变量
                TestLabel.dimensionTaskId = dimension_task_id

                # 记录到报告
                allure.attach(
                    f"找到任务: {self.task_name}\n"
                    f"dimensionTaskId: {dimension_task_id}",
                    name="任务匹配结果",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                # 记录错误信息
                error_msg = f"错误: 未找到名称为 '{self.task_name}' 的任务"
                allure.attach(error_msg, name="任务查找失败", attachment_type=allure.attachment_type.TEXT)

                # 抛出异常
                pytest.fail(error_msg)

        with allure.step("步骤5：追加标注任务") as step5:
            # 记录追加任务参数
            append_params = (
                f"任务ID: {self.dimensionTaskId}\n"
                f"样本ID: {self.sampleDataSyncId_2}\n"
            )
            allure.attach(append_params, name="追加标注任务参数", attachment_type=allure.attachment_type.TEXT)

            response = self.api_bash_sample.append_label_task(startDateTime, endDateTime, [self.sampleDataSyncId_2],
                                                              self.dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

        with allure.step("步骤6：ok图创建提交数据集") as step6:
            # 记录数据集参数
            dataset_params = (
                f"数据集名称: 接口自动化ok图-{time_str}\n"
                f"样本ID: {self.sampleDataSyncId_3}\n"
            )
            allure.attach(dataset_params, name="创建数据集参数", attachment_type=allure.attachment_type.TEXT)

            response = self.api_bash_sample.ok_graph_create_dataset(f"接口自动化ok图-{time_str}", startDateTime,
                                                                    endDateTime, [self.sampleDataSyncId_3])
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

    @pytest.mark.order(2)
    @allure.story("2D标注")
    def test_2d_label(self):
        # 使用类变量
        dimensionTaskId = TestLabel.dimensionTaskId

        with allure.step("步骤1：查询2D标注任务是否存在") as step1:
            response = self.api_2d_label.query_2d_task(self.task_name)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 检查任务列表中是否存在指定任务名的任务
            task_list = response_data.get('data', {}).get('list', [])
            task_exists = any(task.get('taskName') == self.task_name for task in task_list)

            if not task_exists:
                error_msg = f"错误: 未找到任务名称为 '{self.task_name}' 的任务"
                allure.attach(error_msg,
                              name="任务查找失败",
                              attachment_type=allure.attachment_type.TEXT)
                pytest.fail(error_msg)
            else:
                allure.attach(f"成功找到任务: {self.task_name}",
                              name="任务验证结果",
                              attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤2：开始标注") as step2:
            response = self.api_2d_label.re_label(dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(2, "进行中")

        with allure.step("步骤3：查询标注图片获取datasetDataId") as step3:
            response = self.api_2d_label.query_2d_sample(dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 获取前两条数据的datasetDataId
            sample_list = response_data.get('data', {}).get('list', [])
            if len(sample_list) >= 2:
                TestLabel.datasetDataId_1 = sample_list[0].get('datasetDataId')
                TestLabel.datasetDataId_2 = sample_list[1].get('datasetDataId')

                # 记录到Allure报告
                extracted_data = (
                    f"提取的前两条datasetDataId:\n"
                    f"1. {TestLabel.datasetDataId_1}\n"
                    f"2. {TestLabel.datasetDataId_2}"
                )
                allure.attach(extracted_data,
                              name="提取的datasetDataId",
                              attachment_type=allure.attachment_type.TEXT)
            else:
                error_msg = "错误: 响应数据不足2条，无法提取全部datasetDataId"
                allure.attach(error_msg,
                              name="数据提取失败",
                              attachment_type=allure.attachment_type.TEXT)
                pytest.fail(error_msg)

        with allure.step("步骤4：标注矩形") as step4:
            # 记录标注参数到Allure
            label_params = (
                f"标注参数:\n"
                f"datasetDataId: {self.datasetDataId_1}\n"
                f"标签: 拉伤\n"
                f"形状: 矩形\n"
                f"坐标: [[78, 57], [128, 83]]\n"
                f"争议: 无争议"
            )
            allure.attach(label_params,
                          name="矩形标注参数",
                          attachment_type=allure.attachment_type.TEXT)

            response = self.api_2d_label.label_2d_rectangle(self.datasetDataId_1, "lashang", "rectangle",
                                                            [[78, 57], [128, 83]],
                                                            "")
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 记录标注结果
            allure.attach(f"标注结果: {response_data['msg']}",
                          name="矩形标注结果",
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤5：标注多边形") as step5:
            # 记录标注参数到Allure
            label_params = (
                f"标注参数:\n"
                f"datasetDataId: {self.datasetDataId_2}\n"
                f"标签: 脱模\n"
                f"形状: 多边形\n"
                f"坐标: [[160, 64], [110, 116], [118, 222], [268, 242], [308, 138], [244, 60]]\n"
                f"争议: 有争议"
            )
            allure.attach(label_params,
                          name="多边形标注参数",
                          attachment_type=allure.attachment_type.TEXT)

            response = self.api_2d_label.label_2d_polygon(self.datasetDataId_2, "tuomo", "polygon",
                                                          [[160, 64], [110, 116], [118, 222], [268, 242], [308, 138],
                                                           [244, 60]],
                                                          "")
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 记录标注结果
            allure.attach(f"标注结果: {response_data['msg']}",
                          name="多边形标注结果",
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤6：判断2D标注任务是否完成") as step6:
            response = self.api_2d_label.query_2d_task(self.task_name)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            # 查找指定任务名的任务
            task_list = response_data.get('data', {}).get('list', [])
            target_task = None

            for task in task_list:
                if task.get('taskName') == self.task_name:
                    target_task = task
                    break

            if target_task:
                # 检查未标注数量
                no_tag_num = target_task.get('noTagNum', -1)  # 默认-1表示未获取到

                # 记录任务信息到报告
                task_info = (
                    f"任务名称: {self.task_name}\n"
                    f"未标注数量(noTagNum): {no_tag_num}\n"
                    f"预期值: 0"
                )
                allure.attach(task_info,
                              name="任务标注状态检查",
                              attachment_type=allure.attachment_type.TEXT)

                if no_tag_num == 0:
                    allure.attach("标注完成: 未标注数量为0",
                                  name="标注状态验证结果",
                                  attachment_type=allure.attachment_type.TEXT)
                else:
                    error_msg = f"错误: 未标注数量({no_tag_num})大于0，标注未完成！"
                    allure.attach(error_msg,
                                  name="标注状态验证失败",
                                  attachment_type=allure.attachment_type.TEXT)
                    pytest.fail(error_msg)
            else:
                error_msg = f"错误: 未找到任务名称为 '{self.task_name}' 的任务"
                allure.attach(error_msg,
                              name="任务查找失败",
                              attachment_type=allure.attachment_type.TEXT)
                pytest.fail(error_msg)

        with allure.step("步骤7：提交复核") as step7:
            response = self.api_2d_label.submit_review(dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(3, "待复核")

        with allure.step("步骤8：复核不通过") as step8:
            response = self.api_2d_label.review_judge(dimensionTaskId, 8)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(8, "复核未通过")

        with allure.step("步骤9：重标") as step9:
            response = self.api_2d_label.re_label(dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(2, "进行中")

        with allure.step("步骤10：再次提交复核") as step10:
            response = self.api_2d_label.submit_review(dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(3, "待复核")

        with allure.step("步骤11：复核通过") as step11:
            response = self.api_2d_label.review_judge(dimensionTaskId, 4)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(4, "复核通过")

        with allure.step("步骤12：创建&提交数据集") as step12:
            response = self.api_2d_label.create_dataset(self.task_name, dimensionTaskId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            self.verify_task_status(5, "已提交")
