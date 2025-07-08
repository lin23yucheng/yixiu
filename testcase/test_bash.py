"""
验证bash系统挑图
"""
import configparser
import allure

from api import api_bash
from common import Assert
from datetime import datetime
from common.Request_Response import ApiClient

assertions = Assert.Assertions()

# 读取配置
config = configparser.ConfigParser()
config.read("./config/env_config.ini")
section_one = "global"
section_two = "bash"
miai_product_code = config.get(section_one, "miai-product-code")
miaispacemanageid = config.get(section_one, "miaispacemanageid")
admin_account = config.get(section_two, "admin_account")
admin_password = config.get(section_two, "admin_password")
myself_name = config.get(section_two, "myself_name")

# 格式化时间
current_date = datetime.now().strftime("%Y-%m-%d")
end_time = f"{current_date}T23:59:00.000Z"
start_time = f"{current_date}T00:00:00.000Z"

# 管理员账号
base_headers = {"Authorization": api_bash.ApiBashSample.bash_login(admin_account, admin_password)}
global_client = ApiClient(base_headers=base_headers)


@allure.feature("场景：Bash系统检查配置信息")
class TestBash:

    @classmethod
    def setup_class(cls):
        cls.api_bash = api_bash.ApiBashSample(global_client)
        cls.myself_id = None

    @allure.story("登录管理员账号验证配置信息")
    def test_verify_product(self):
        with allure.step("步骤1：查看产品是否存在"):
            response = self.api_bash.query_product_manage(miaispacemanageid, miai_product_code)
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 检查是否有数据
            if 'data' not in data or not data['data'].get('list'):
                error_msg = "bash产品管理中没有对应的产品"
                allure.attach(error_msg, name="产品缺失错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 获取第一个产品
            first_product = data['data']['list'][0]
            setting_status = first_product.get('settingStatus')

            # 检查产品状态
            if setting_status != 1:
                error_msg = f"产品状态异常（当前状态: {setting_status}），请登录bash系统查看"
                allure.attach(error_msg, name="产品状态错误", attachment_type=allure.attachment_type.TEXT)
                allure.attach(str(first_product), name="产品详情", attachment_type=allure.attachment_type.JSON)
                raise AssertionError(error_msg)

        with allure.step("步骤2：查看bash人员是否存在"):
            response = self.api_bash.query_personnel_id()
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 新增人员存在性检查
            if 'data' not in data or not data['data'].get('list'):
                error_msg = "人员列表为空"
                allure.attach(error_msg, name="人员列表为空错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 在人员列表中查找指定用户名的人员
            target_person = None
            for person in data['data']['list']:
                # 假设人员对象中有 'username' 字段
                if person.get('username') == myself_name:  # 使用配置文件中读取的 myself_name
                    target_person = person
                    break

            if not target_person:
                error_msg = f"bash分拣账号的人员 {myself_name} 不存在"
                allure.attach(error_msg, name="人员不存在错误", attachment_type=allure.attachment_type.TEXT)
                allure.attach(str(data['data']['list']), name="人员列表详情",
                              attachment_type=allure.attachment_type.JSON)
                raise AssertionError(error_msg)

            # 获取人员ID
            person_id = target_person.get('id')
            if not person_id:
                error_msg = f"找到人员 {myself_name} 但未获取到ID"
                allure.attach(error_msg, name="ID缺失错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 记录人员ID到Allure报告
            allure.attach(f"人员 {myself_name} 的ID: {person_id}",
                          name="人员ID信息",
                          attachment_type=allure.attachment_type.TEXT)

            # 将人员ID存储到类属性中
            self.myself_id = person_id

        with allure.step("步骤3：查看人员与产品是否关联"):
            response = self.api_bash.query_product_manage_person(self.myself_id)
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 检查是否有数据
            if 'data' not in data or not data['data'].get('list'):
                error_msg = "坐席人员列表为空"
                allure.attach(error_msg, name="人员列表为空错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 遍历人员列表，查找是否存在目标产品代码
            found = False
            for person in data['data']['list']:
                # 注意：这里假设每个人员对象中有'productCode'字段
                if person.get('productCode') == miai_product_code:
                    found = True
                    break

            if not found:
                error_msg = f"坐席人员没有添加对应的产品: {miai_product_code}"
                allure.attach(error_msg, name="产品缺失错误", attachment_type=allure.attachment_type.TEXT)
                allure.attach(str(data['data']['list']), name="人员列表详情",
                              attachment_type=allure.attachment_type.JSON)
                raise AssertionError(error_msg)

        with allure.step("步骤3：查看人员计划"):
            response = self.api_bash.query_personnel_plan()
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 检查是否存在当日数据（合并无数据和有数据但无当日数据的情况）
            target_date = f"{current_date}T00:00:00"

            # 初始化标志
            has_today_plan = False

            # 只有当有数据时才检查
            if 'data' in data and data['data'].get('list'):
                for plan in data['data']['list']:
                    if plan.get('startTime') == target_date:
                        has_today_plan = True
                        break

            # 如果没有当日数据（包括无数据的情况），执行生成操作
            if not has_today_plan:
                with allure.step("子步骤1：生成人员计划（无当日数据时触发）"):
                    # 调用生成人员计划方法
                    response = self.api_bash.create_personnel_plan(end_time, start_time)
                    assertions.assert_code(response.status_code, 200)
                    data = response.json()
                    assertions.assert_in_text(data['msg'], '操作成功')

                    # 记录操作信息到报告
                    allure.attach(f"已生成当日({current_date})人员计划",
                                  name="生成人员计划成功",
                                  attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤4：查看人员排班"):
            response = self.api_bash.query_personnel_schedule(end_time, start_time)
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 初始化标志
            found_user = False

            # 检查是否存在指定人员（即使数据为空也会执行）
            if 'data' in data and data['data'].get('selectedUserListVos'):
                for user in data['data']['selectedUserListVos']:
                    if user.get('userName') == "林禹成":
                        found_user = True
                        break

            if not found_user:
                with allure.step("子步骤1：修改人员排班（缺少林禹成时触发）"):
                    # 获取toBeSelectedUserListVos中的所有ID
                    to_be_selected = data['data'].get('toBeSelectedUserListVos', [])
                    userid_list = [str(user.get('id')) for user in to_be_selected if user.get('id')]

                    # 拼接ID列表为字符串格式
                    userid_list_str = "[" + ", ".join(f'"{id}"' for id in userid_list) + "]"

                    # 记录ID列表到Allure报告
                    allure.attach(f"待选用户ID列表: {userid_list_str}",
                                  name="待选用户ID",
                                  attachment_type=allure.attachment_type.TEXT)

                    # 调用修改人员排班方法
                    response = self.api_bash.update_personnel_schedule(end_time, start_time, userid_list)
                    assertions.assert_code(response.status_code, 200)
                    data = response.json()
                    assertions.assert_in_text(data['msg'], '操作成功')

                    # 记录操作信息到报告
                    allure.attach("已将林禹成添加到当日排班",
                                  name="修改人员排班",
                                  attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤5：验证排班状态"):
            response = self.api_bash.query_personnel_plan()
            assertions.assert_code(response.status_code, 200)
            data = response.json()
            assertions.assert_in_text(data['msg'], '操作成功')

            # 检查是否有数据
            if 'data' not in data or not data['data'].get('list'):
                error_msg = "人员计划数据为空"
                allure.attach(error_msg, name="计划数据为空错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 查找当日计划
            today_plan = None
            for plan in data['data']['list']:
                if plan.get('startTime') == start_time.replace('.000Z', ''):  # 去掉毫秒部分以匹配格式
                    today_plan = plan
                    break

            if not today_plan:
                error_msg = f"未找到当日({current_date})人员计划"
                allure.attach(error_msg, name="计划缺失错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)

            # 检查发布状态
            is_release = today_plan.get('isRelease')
            if is_release == 0:
                with allure.step("子步骤1：发布排班（未发布时触发）"):
                    # 调用发布排班方法
                    response = self.api_bash.release_personnel_schedule(end_time.replace('.000Z', ''),
                                                                        start_time.replace('.000Z', ''))
                    assertions.assert_code(response.status_code, 200)
                    data = response.json()
                    assertions.assert_in_text(data['msg'], '操作成功')

                    # 记录操作信息到报告
                    allure.attach(f"已发布当日({current_date})排班",
                                  name="发布排班成功",
                                  attachment_type=allure.attachment_type.TEXT)
            elif is_release == 1:
                with allure.step("排班已发布，结束测试"):
                    allure.attach(f"当日({current_date})排班已发布",
                                  name="排班状态",
                                  attachment_type=allure.attachment_type.TEXT)
            else:
                error_msg = f"未知的排班状态: {is_release}"
                allure.attach(error_msg, name="排班状态错误", attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(error_msg)
